from .http import HTTPClient
from .constants import Endpoints, Actions, Events, RoomActions
from .socket import SocketClient, DubtrackMessage, RoomActionMessage
from ..models import *
import asyncio
import logging

class Client:
    """
    The client class is the main class you should be using to communicate with the Dubtrack API.
    It provides methods for handling events and non-room-specific functions.
    
    All parameters are optional.
    
    .. _aiohttp: http://aiohttp.readthedocs.io/en/stable/index.html
    
    Parameters
    ----------
    connector: :class:`aiohttp.BaseConnector`
        A custom `aiohttp`_ connector may be passed if desired. This is to allow proxying.
    proxy_options: :class:`ProxyOptions`
        Proxy options, if proxying is required.
    recent_conversations: bool
        If True, calls :meth:`Client.fetch_conversations` after you have logged in. Defaults to True.
    
    Attributes
    ----------
    user: :class:`AuthenticatedUser`
        The logged-in user. Populated after a successful `login` call, None otherwise.
    logged_in: bool
        True if logged in, False otherwise.
    rooms: :class:`RoomCollection`
        Cached rooms that the bot has joined at least once this session.
    users: :class:`Collection`
        Cached users the bot has seen.
    messages: :class:`MessageCollection`
        Messages received during this session.
    """
    def __init__(self, **kwargs):
        self._log = logging.getLogger("backtracked")

        self.loop = asyncio.get_event_loop()
        self.http = HTTPClient(self.loop, connector=kwargs.get("connector", None),
                               proxy_options=kwargs.get("proxy_options", None))
        self.user = None

        self.socket = SocketClient(self)
        self.logged_in = False
        self.connection_id = None
        self._recent_conversations = kwargs.get("recent_conversations", True)

        self.event_handlers = {}

        self.rooms = RoomCollection()
        self.users = UserCollection()
        self.messages = MessageCollection()
        self.song_cache = Collection()
        self.conversations = ConversationCollection()

    def event(self, coro):
        """
        Decorator used for registering event handlers.
        """
        if asyncio.iscoroutinefunction(coro):
            event_name = coro.__name__

            if event_name not in self.event_handlers:
                self.event_handlers[event_name] = []

            self.event_handlers[event_name].append(coro)
        else:
            raise BaseException("Passed function wasn't a coroutine!")

    def _dispatch(self, ev_name, *payload):
        if ev_name not in self.event_handlers:
            return

        for callback in self.event_handlers[ev_name]:
            try:
                self.loop.create_task(callback(*payload))
            except BaseException as err:
                self._log.error("Error executing callback {name}: {err}"
                                .format(name=callback.__name__, err=err.with_traceback(err.__traceback__)))

    # LOGIN + CONNECT #

    async def login(self, email: str, password: str):
        """
        Log in to Dubtrack. This does not connect to the websocket.
        
        Parameters
        ----------
        email: str
            Bot email
        password: str
            Bot password
        """
        await self.http.post(Endpoints.auth_dubtrack, data={"username": email, "password": password})
        _, user_raw = await self.http.get(Endpoints.auth_session)
        self.user = AuthenticatedUser.from_data(self, user_raw)

        self.logged_in = True

        if self._recent_conversations:
            self.loop.create_task(self.fetch_conversations())

    async def connect(self):
        """
        Connect to the Dubtrack websocket. You must call login first.
        """
        _, resp = await self.http.get(Endpoints.auth_token)
        await self.socket.connect(resp["token"])

    def run(self, email, password):
        """
        Log in to Dubtrack and connect to the websocket. This call is blocking, and abstracts away event loop
        creation. If you need more control over the event loop, use login and connect.
        
        Parameters
        ----------
        email: str
            Bot email
        password: str
            Bot password
        """
        try:
            self.loop.run_until_complete(self.login(email, password))
            self.loop.run_until_complete(self.connect())
        except KeyboardInterrupt:
            self.close()
            pending = asyncio.Task.all_tasks(loop=self.loop)
            gathered = asyncio.gather(*pending, loop=self.loop)

            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)
                gathered.exception()
            except:
                pass
        finally:
            self.loop.close()

    def close(self):
        self.http.session.close()
        self.logged_in = False

    # API #

    async def join_room(self, room_slug: str) -> Room:
        """
        Join a Dubtrack room via its URL slug.
        
        Parameters
        ----------
        room_slug: str
            the room's slug

        Returns
        -------
        :class:`Room`
            Room object of the joined room 
        """
        _, room_raw = await self.http.get(Endpoints.room_join(slug=room_slug))
        room = Room(self, room_raw)
        self.rooms.add(room)

        _, member_data = await self.http.post(Endpoints.room_users(rid=room.id))
        room.members.add(Member(self, member_data.get("user", {})))

        self.loop.create_task(self._backfill_room(room))

        await self.socket.send(action=Actions.join_room, channel=room.room_id)
        return room

    async def fetch_conversations(self):
        """
        Fetch currently open conversations from Dubtrack.
        
        This method is called automatically if the parameter `recent_conversations` is True
        when initializing this :class:`Client`.
        """
        _, conversations = await self.http.get(Endpoints.conversations)

        for conv_data in conversations:
            conv = Conversation(self, conv_data)
            self.conversations.add(conv)

    # INTERNAL HANDLING #

    async def _backfill_room(self, room: Room):
        _, user_list = await self.http.get(Endpoints.room_users(rid=room.id))

        for member_data in user_list:
            user = User(self, member_data.get("_user", {}))
            member = Member(self, member_data)
            self.users.add(user)
            room.members.add(member)

    def _handle_payload(self, payload: DubtrackMessage):
        self._log.debug("WS Recv: {0.action.name} - {0.data}".format(payload))

        if payload.action == Actions.connected:
            self.connection_id = payload.connectionId

            self._dispatch(Events.on_ready)
        elif payload.action == Actions.joined_room:
            room = self.rooms.from_room_id(payload.channel)

            if room is not None:
                self._dispatch(Events.on_joined_room, room)
        elif payload.action == Actions.presence_change:
            room = self.rooms.from_room_id(payload.channel)
            user = self.users.get(payload.presence.get("clientId"))
            # TODO: Still not sure if we should cache members...

            if user is not None:
                self._dispatch(Events.on_member_presence, room, user)
        elif payload.action == Actions.room_action:
            msg = RoomActionMessage(payload.message)

            if payload.channel.startswith('room:'):
                room = self.rooms.from_room_id(payload.channel)
                self._handle_room_action(room=room, msg=msg)
            elif payload.channel.startswith('user:'):
                user = self.users.from_channel(payload.channel)
                self._handle_user_action(user=user, msg=msg)

    def _handle_room_action(self, room: Room, msg: RoomActionMessage):
        if msg.name == RoomActions.chat_message:
            user = User(self, msg.value.user)
            self.users.add(user)
            message = Message(self, msg.value.data)
            self.messages.add(message)

            self._dispatch(Events.on_chat, message)
        elif msg.name == RoomActions.chat_skip:
            pass  # TODO: Handle this once we cache the playlist?
        elif msg.name == RoomActions.chat_delete:
            user = User(self, msg.value.user)
            self.users.add(user)
            message = self.messages.get(msg.value.chatid)

            if message is not None:
                message.deleted = True
                self._dispatch(Events.on_chat_delete, message)
        elif msg.name == RoomActions.room_playlist_dub:
            song = Song(self, msg.value.playlist)
            user = User(self, msg.value.user)
            self.users.add(user)
            dubtype = msg.value.dubtype

            self._dispatch(Events.on_dub, song, user, dubtype)
        elif msg.name == RoomActions.room_playlist_update:
            song_info = SongInfo(msg.value.songInfo)
            self.song_cache.add(song_info)
            song = Song(self, msg.value.song)
            room.playlist.append(song)

            self._dispatch(Events.on_playlist_song_add, song)
        elif msg.name == RoomActions.user_join:
            user = User(self, msg.value.user)
            self.users.add(user)
            member = Member(self, msg.value.roomUser)
            room.members.add(member)

            self._dispatch(Events.on_member_join, member)
        elif msg.name == RoomActions.user_update:
            member = Member(self, msg.value.user)
            room.members.add(member)

            self._dispatch(Events.on_member_update, member)

    def _handle_user_action(self, user: User, msg: RoomActionMessage):
        if msg.name == RoomActions.new_message:
            sender_id = msg.value.userid

            if sender_id == self.user.id:
                return

            sender = self.users.get(sender_id)

            self._dispatch(Events.on_private_message, sender)
