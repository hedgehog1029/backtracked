from .base import Model
import datetime

class User(Model):
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.username = data.get("username")
        self.created_at = datetime.datetime.fromtimestamp(data.get("created") / 1000)
        self.status = data.get("status")
        self.dubs = data.get("dubs")
        self._roleid = data.get("roleid")

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
        self.avatar_url = data.get("profileImage", {}).get("url")
