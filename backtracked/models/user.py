from .base import Model, Collection
from ..client.constants import Role, Endpoints
from .. import utils
import datetime

__all__ = ["User", "AuthenticatedUser", "Member"]

class User(Model):
    """
    Represents a specific user on Dubtrack.

    Attributes
    ----------
    id: str
        ID of this user.
    username: str
        User's chosen username.
    created_at: `datetime.datetime`
        Datetime representing the date when this user created their account.
    avatar_url: str
        URL of this user's avatar.
    """
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

    def member_of(self, room):
        """
        Returns the :class:`Member` object of this user in the given :class:`Room`. May be None if the member hasn't
        yet been backfilled.
        :param room: :class:`Room` of the sought-after member.
        :return: :class:`Member`
        """
        return room.members.from_user_id(self.id)

    @classmethod
    def from_data(cls, client, data: dict):
        return cls(client, data)

class AuthenticatedUser(User):
    def __init__(self, client, data: dict):
        super().__init__(client, data)

    async def update_profile(self, **kwargs):
        pass

class Member(Model):
    """
    Represents a Dubtrack user's data from a specific :class:`Room`.
    This does not subclass :class:`User`, as Dubtrack itself does not count them as the same entity.
    Instead, the `user` getter should be used for retrieving the associated user.

    Attributes
    ----------
    id: str
        The ID of this member.
    dubs: int
        Total dubs this member has received in the associated :class:`Room`
    order: int
        Location of this user in the queue
    authorized: bool
        No idea tbh
    skipped: int
        Number of songs queued by this member that have been skipped.
    played: int
        Number of songs queued by this member that have been played.
    queued_now: int
        Number of songs in the current queue queued by this member.
    wait_line: int
        ?????
    banned: bool
        True if this member is banned, False otherwise
    banned_time: `datetime.datetime`
        Datetime representing the time this member was banned. Useless if `banned` is False.
    banned_until: `datetime.datetime`
        Datetime representing the time this member will be unbanned. Useless if `banned` is False.
    user: :class:`User`
        User object associated with this member object.
    room: :class:`Room`
        Room object associated with this member object.
    role: :class:`Role`
        Role enum representing this member's assigned role, or None if no role has been assigned.
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.dubs = data.get("dubs")
        self.order = data.get("order")
        self.authorized = data.get("authorized")
        self.queue_paused = data.get("queuePaused", False)
        self.active = data.get("active")
        self.skipped = data.get("skippedCount")
        self.played = data.get("playedCount")
        self.queued_now = data.get("songsInQueue")
        self.wait_line = data.get("waitLine", 0)
        self.banned = data.get("banned", False)
        self.banned_time = utils.dt(data.get("bannedTime", 0))
        self.banned_until = utils.dt(data.get("bannedUntil", 0))

        self._roleid = data.get("roleid", {}).get("_id")
        self._roomid = data.get("roomid")
        self._userid = data.get("userid")

    @property
    def user(self):
        """
        Gets the user associated with this member.
        :return: User behind this Member
        """
        return self.client.users.get(self._userid)

    @property
    def room(self):
        """
        Gets the room this member object is assigned to.
        :return: Room of this member
        """
        return self.client.rooms.get(self._roomid)

    @property
    def role(self) -> Role:
        """
        Get this user's assigned role, or None if the user has no role.
        :return: :class:`Role` enum or None
        """
        return Role.from_id(self._roleid)

    async def set_role(self, role: Role):
        """
        Sets the role of this member, if the bot has the required right.

        :param role: Role
        :return:
        """
        _, raw = await self.client.http.post(Endpoints.member_set_role(roleid=role.value.id, rid=self._roomid,
                                                                       uid=self._userid),
                                             data={"realTimeChannel": self.room.rtc})
        print(raw)

class MemberCollection(Collection):
    def from_user_id(self, user_id: str):
        return utils.get(self.values(), _userid=user_id)
