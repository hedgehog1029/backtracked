from .base import Model, OrderedCollection
from .user import Member, User
from .room import Room
from ..client.constants import Endpoints
from .. import utils

__all__ = ["Message", "MessageCollection"]

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
        If this 
        
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
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.created_at = utils.dt(data.get("created"))
        self._users = data.get("usersid")
        self._latest_message = data.get("latest_message")
        self._latest_message_str = data.get("latest_message_str")
        self._read = data.get("users_read")

    @property
    def _recipient(self):
        others = filter(lambda uid: self.client.user.id != uid, self._users)
        return next(others)

    @property
    def recipient(self) -> User:
        """
        Get the primary recipient of this conversation.
        
        Returns
        -------
        :class:`User`
            Recipient of this conversation.
        """
        return self.client.users.get(self._recipient)

    async def fetch(self) -> list:
        """
        Fetch all messages for this conversation.
        
        Returns
        -------
        list[str]
            List of message IDs in this conversation.
        """
        _, messages = await self.client.http.get(Endpoints.conversation(cid=self.id))
        self._latest_message = messages[0]['_id']
        self._latest_message_str = messages[0]['']

        for msg_data in messages:
            message = Message.from_conversation_message(self.client, msg_data)

            self.client.messages.add(message)

        return list(map(lambda m: m['_id'], messages))

    def get_latest_message(self) -> Message:
        """
        Get the latest message. Does not fetch messages from Dubtrack.
        If you want to be sure you're getting the latest messages, call :meth:`Client.fetch_conversations` or
        :meth:`Conversation.fetch` first.
        
        Returns
        -------
        :class:`Message`
            Latest message in this conversation.
        """
        return self.client.messages.get(self._latest_message)

    def has_read(self, user: User) -> bool:
        return user.id in self._read

class MessageCollection(OrderedCollection):
    pass
