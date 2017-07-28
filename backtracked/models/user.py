from .base import Model, Collection
from ..client.constants import Role, Endpoints
from .. import utils
import datetime
import logging

__all__ = ["User", "AuthenticatedUser", "Member"]
logger = logging.getLogger("backtracked.models.user")

class User(Model):
    """
    Represents a specific user on Dubtrack.

    Attributes
    ----------
    id: str
        ID of this user.
    username: str
        User's chosen username.
    created_at: :class:`datetime.datetime`
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
    async def open_conversation(self):
        """
        Opens a conversation with this user. Will re-use a previous conversation if the bot has one cached.
        
        Returns
        -------
        :class:`Conversation`
            A conversation with this user as the recipient.
        """
        from .message import Conversation
        conv = utils.get(self.client.conversations.values(), _recipient=self.id)

        if conv is None:
            _, raw = await self.client.http.post(Endpoints.conversations, data={"usersid": [self.id]})
            conv = Conversation(self.client, raw)

        return conv

    def member_of(self, room):
        """
        Returns the :class:`Member` object of this user in the given :class:`Room`. May be None if the member hasn't
        yet been backfilled.
        
        Parameters
        ----------
        room: :class:`Room`
            Room of the sought-after member.
        
        Returns
        -------
        :class:`Member`
            Requested member or None.
        """
        return room.members.from_user_id(self.id)

    @classmethod
    def from_data(cls, client, data: dict):
        return cls(client, data)

class AuthenticatedUser(User):
    """
    Represents the logged-in user. Subclass of :class:`User`, and inherits all its properties.
    """
    def __init__(self, client, data: dict):
        super().__init__(client, data)

    async def update_profile(self, **kwargs):
        pass

    async def change_username(self, username):
        """
        Change this account's username.
        
        Parameters
        ----------
        username: str
            New username to use

        Returns
        -------
        bool
            True if the username was successfully changed, False otherwise.
        """
        status, _ = await self.client.http.post(Endpoints.user_update_username, data={"username": username})

        if status == 200:
            return True
        else:
            return False

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
    banned_time: :class:`datetime.datetime`
        Datetime representing the time this member was banned. Useless if `banned` is False.
    banned_until: :class:`datetime.datetime`
        Datetime representing the time this member will be unbanned. Useless if `banned` is False.
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

        if isinstance(data.get("roleid"), str):
            self._roleid = data.get("roleid")
        elif isinstance(data.get("roleid"), dict):
            self._roleid = data.get("roleid", {}).get("_id")

        self._roomid = data.get("roomid")
        self._userid = data.get("userid")

    @property
    def user(self):
        """
        User object associated with this member object.
        
        Returns
        -------
        :class:`User`
            User behind this Member
        """
        return self.client.users.get(self._userid)

    @property
    def room(self):
        """
        Gets the room this member object is assigned to.
        
        Returns
        -------
        :class:`Room`
            Room of this member
        """
        return self.client.rooms.get(self._roomid)

    @property
    def role(self) -> Role:
        """
        Get this user's assigned role, or None if the user has no role.
        
        Returns
        -------
        :class:`Role`
            Assigned role of this member.
        """
        return Role.from_id(self._roleid)

    async def set_role(self, role: Role):
        """
        Sets the role of this member, if the bot has the required right.

        Parameters
        ----------
        role: :class:`Role`
            Role to give the member.
        """
        _, raw = await self.client.http.post(Endpoints.member_set_role(roleid=role.value.id, rid=self._roomid,
                                                                       uid=self._userid),
                                             data={"realTimeChannel": self.room.rtc})
        print(raw)

class MemberCollection(Collection):
    def from_user_id(self, user_id: str):
        return utils.get(self.values(), _userid=user_id)
