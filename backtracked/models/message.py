from .base import Model, OrderedCollection
from .user import Member, User
from .room import Room
from ..client.constants import Endpoints
from .. import utils

__all__ = ["Message", "MessageCollection", "Conversation", "ConversationCollection"]

def everything_except(iterable, exception):
    return filter(lambda o: o != exception, iterable)

class Message(Model):
    """
    Represents a sent message on Dubtrack.
    
    Attributes
    ----------
    id: str
        Chat ID of this message.
    content: str
        Text of the message.
    deleted: bool
        True if the message has been deleted, False otherwise.
    created_at: :class:`datetime.datetime`
        Datetime representing the time this message was sent.
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("chatid")
        self.content = data.get("message")
        self.deleted = False
        self.created_at = utils.dt(data.get("time"))
        self._userid = data.get("user", {}).get("_id")
        self._roomid = data.get("queue_object", {}).get("roomid")
        # self.member = Member(self, data.get("queue_object"))  # today on naming things with dubtrack

    @classmethod
    def from_conversation_message(cls, client, data: dict):
        new_data = dict(chatid=data.get("_id"),
                        message=data.get("message"),
                        time=data.get("created"),
                        user=data.get("_user"),
                        queue_object={"roomid": None})
        return cls(client, new_data)

    @property
    def author(self) -> User:
        """
        Get the author of this message.
        
        Returns
        -------
        :class:`User`
            Author of this message
        """
        return self.client.users.get(self._userid)

    @property
    def room(self) -> Room:
        """
        Get the room this message was sent in.
        If this message was sent in a private conversation, this will be None.
        
        Returns
        -------
        :class:`Room`
            Room this message was sent to.
        """
        return self.client.rooms.get(self._roomid)

    @property
    def member(self) -> Member:
        """
        Get the author of this message as a member of the room.
        
        Returns
        -------
        :class:`Member`
            Member who sent this message.
        """
        return self.room.members.from_user_id(self._userid)

# TODO: Conversations can actually have multiple recipients.
class Conversation(Model):
    """
    Represents a private conversation between two users.
    
    Attributes
    ----------
    id: str
        ID of this conversation.
    created_at: :class:`datetime.datetime`
        Time this conversation was started.
    latest_message_str: str
        Text of the last message to be sent in this conversation. May not be up-to-date unless :meth:`fetch` is called.
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.created_at = utils.dt(data.get("created"))
        self.latest_message_str = data.get("latest_message_str")
        self._latest_message_dt = data.get("latest_message")
        self._read = data.get("users_read")
        self._users = []

        for user in data.get("usersid"):
            u = User(self.client, user)
            self._users.append(u.id)
            self.client.users.add(u)

    @property
    def _recipients(self):
        others = everything_except(self._users, self.client.user.id)
        return list(others)

    @property
    def recipients(self) -> list:
        """
        Get the recipients of this conversation.
        
        Returns
        -------
        list[:class:`User`]
            Recipients of this conversation.
        """
        return list(map(self.client.users.get, self._recipients))

    async def fetch(self) -> list:
        """
        Fetch all messages for this conversation.
        
        Returns
        -------
        list[str]
            List of message IDs in this conversation.
        """
        _, messages = await self.client.http.get(Endpoints.conversation(cid=self.id))
        self.latest_message_str = messages[0]['message']

        for msg_data in messages:
            message = Message.from_conversation_message(self.client, msg_data)

            self.client.messages.add(message)

        return list(map(lambda m: m['_id'], messages))

    async def send_message(self, text: str):
        """
        Send a message to this conversation.
        
        Parameters
        ----------
        text: str
            Text to send in the message.
        """
        data = {
            "message": text,
            "userid": self.client.user.id
        }

        _, msg_data = await self.client.http.post(Endpoints.conversation(cid=self.id), json=data)
        # TODO: fuck me the message data is in yet *another* format
        # we'll deal with this later

    async def mark_as_read(self):
        """
        Marks this conversation as read by the current user.
        """
        _, resp = await self.client.http.post(Endpoints.conversation_read(cid=self.id))

        self._read = resp.get("users_read")

    def has_read(self, user: User) -> bool:
        """
        Checks if the passed :class:`User` has read this conversation.
        
        Parameters
        ----------
        user: :class:`User`
            User to check

        Returns
        -------
        bool:
            True if the user has read this conversation, False otherwise.
        """
        return user.id in self._read

class MessageCollection(OrderedCollection):
    pass

class ConversationCollection(OrderedCollection):
    def get_by_recipients(self, *args):
        def _checker(conv: Conversation):
            for uid in args:
                if uid not in conv._recipients:
                    return False
            return True

        convs = filter(_checker, self.values())
        return next(convs, None)
