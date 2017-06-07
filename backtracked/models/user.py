from .base import Model
from .. import utils
import datetime

__all__ = ["User", "AuthenticatedUser", "Member"]

class User(Model):
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.username = data.get("username")
        self.created_at = utils.dt(data.get("created"))
        self.status = data.get("status")
        self.dubs = data.get("dubs")
        self._roleid = data.get("roleid")
        self.avatar_url = data.get("profileImage", {}).get("url")

    # Some methods to be actually implemented in future
    async def open_pm(self):
        pass

    async def member_of(self, room):
        pass

    @classmethod
    def from_data(cls, client, data: dict):
        return cls(client, data)

class AuthenticatedUser(User):
    def __init__(self, client, data: dict):
        super().__init__(client, data)

class Member(Model):
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.dubs = data.get("dubs")
        self.order = data.get("order")
        self.authorized = data.get("authorized")
        self.queue_paused = data.get("queuePaused")
        self.active = data.get("active")
        self.skipped = data.get("skippedCount")
        self.played = data.get("playedCount")
        self.queued_now = data.get("songsInQueue")
        self.wait_line = data.get("wait_line")

        self._roomid = data.get("roomid")
        self._userid = data.get("userid")

    @property
    def user(self):
        return self.client.users.get(self._userid)

    @property
    def room(self):
        return self.client.rooms.get(self._roomid)
