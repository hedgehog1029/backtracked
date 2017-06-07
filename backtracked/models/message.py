from .base import Model, OrderedCollection
from .user import Member, User
from .room import Room
from .. import utils

__all__ = ["Message", "MessageCollection"]

class Message(Model):
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("chatid")
        self.content = data.get("message")
        self.deleted = False
        self.created_at = utils.dt(data.get("time"))
        self._userid = data.get("user", {}).get("_id")
        self._roomid = data.get("queue_object", {}).get("roomid")
        self.member = Member(self, data.get("queue_object"))  # today on naming things with dubtrack

    @property
    def author(self) -> User:
        return self.client.users.get(self._userid)

    @property
    def room(self) -> Room:
        return self.client.rooms.get(self._roomid)

class MessageCollection(OrderedCollection):
    pass