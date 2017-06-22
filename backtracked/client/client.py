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
    """
    def __init__(self, **kwargs):
        """
        Create a new Client instance.
        :param kwargs: Optional options 
        """
        self.log = logging.getLogger("backtracked")

        self.loop = asyncio.get_event_loop()
        self.http = HTTPClient(self.loop, connector=kwargs.get("connector", None),
                               proxy_options=kwargs.get("proxy_options", None))
        self.user = None

        self.socket = SocketClient(self)
        self.logged_in = False
        self.connection_id = None

        self.event_handlers = {}

        self.rooms = RoomCollection()
        self.users = Collection()
        self.messages = MessageCollection()

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
                self.log.error("Error executing callback {name}: {err}"\
                               .format(name=callback.__name__, err=err.with_traceback(err.__traceback__)))

    # LOGIN + CONNECT #

    async def login(self, email: str, password: str):
        """
        Log in to Dubtrack. This does not connect to the websocket.
        :param email: Bot email
        :param password: Bot password
        """
        await self.http.post(Endpoints.auth_dubtrack, data={"username": email, "password": password})
        _, user_raw = await self.http.get(Endpoints.auth_session)
        self.user = AuthenticatedUser.from_data(self, user_raw)

        self.logged_in = True

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
        :param email: Bot email
        :param password: Bot password
        """
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.login(email, password))
            loop.run_until_complete(self.connect())
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
        :param room_slug: the room's slug
        :return: Room object of the joined room 
        """
        _, room_raw = await self.http.get(Endpoints.room_join(slug=room_slug))
        room = Room(self, room_raw)
        self.rooms.add(room)

        _, res = await self.http.post(Endpoints.room_users(rid=room.id))
        import json
        self.log.debug(json.dumps(res))
        # TODO: this is the only endpoint that returns banned status, so it should be checked here
        # TODO ALSO: the fourth fucking request - possibly schedule this rather than execute here
        # the forth request gets current room users, so it should be used for backfilling
        # still not sure if we're even caching roomusers, though it looks more and more likely
        # TODO: ESPECIALLY if we're backfilling them here! We have access to the Room instance and everything.

        await self.socket.send(action=Actions.join_room, channel=room.room_id)
        return room

    # INTERNAL HANDLING #

    def _handle_payload(self, payload: DubtrackMessage):
        self.log.debug("WS Recv: {0.action.name} - {0.data}".format(payload))

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
            room = self.rooms.from_room_id(payload.channel)
            msg = RoomActionMessage(payload.message)

            self._handle_room_action(room=room, msg=msg)

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
            pass
        elif msg.name == RoomActions.user_join:
            user = User(self, msg.value.user)
            self.users.add(user)
            member = Member(self, msg.value.roomUser)
            room.members.add(member)

            self._dispatch(Events.on_member_join, member)
