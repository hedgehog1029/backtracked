from .base import Model, OrderedCollection
from .user import Member, User
from .room import Room
from .. import utils

__all__ = ["Message", "MessageCollection"]

class Message(Model):
    """
    Represents a sent message on Dubtrack.
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

    @property
    def author(self) -> User:
        """
        Get the author of this message.
        :return: User
        """
        return self.client.users.get(self._userid)

    @property
    def room(self) -> Room:
        """
        Get the room this message was sent in.
        :return: Room
        """
        return self.client.rooms.get(self._roomid)

    @property
    def member(self) -> Member:
        """
        Get the author of this message as a member of the room.
        :return: Member
        """
        return self.room.members.from_user_id(self._userid)

class MessageCollection(OrderedCollection):
    pass