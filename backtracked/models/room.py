from .base import Model, Collection
from .user import MemberCollection
from .. import utils
from ..client.constants import Presence, Actions, Endpoints
from datetime import datetime

__all__ = ["Room", "RoomCollection"]

class Room(Model):
    """
    Represents a room on Dubtrack that may or may not be currently joined.

    Attributes
    ----------
    id: str
        ID of this room.
    name: str
        Name of this room.
    description: str
        Description of this room.
    slug: str
        Slug used for joining this room, seen in the URL upon room join.
    rtc: str
        Real-time channel identifier for this room.
    type: str
        Type of this room
    is_public: bool
        True if this room is public, False otherwise.
    lang: str
        Preferred language for talking in this room. Can be None.
    music_type:
        Music type for this room.
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.slug = data.get("roomUrl")
        self.rtc = data.get("realTimeChannel")
        self.type = data.get("roomType")
        self.is_public = data.get("isPublic")
        self.lang = data.get("lang")
        self.music_type = data.get("musicType")
        self.max_djs = data.get("allowedDjs")
        self.max_song_length = data.get("maxLengthSong")
        self.max_queue_length = data.get("maxSongQueueLength")
        self.dj_recycle = data.get("recycleDJ")
        self.display = RoomDisplaySettings(data)
        self.created_at = utils.dt(data.get("created"))
        self.updated_at = utils.dt(data.get("updated"))
        self.max_repeat_distance = data.get("timeSongQueueRepeat")
        self.active_users = data.get("activeUsers")
        self.queue_locked = data.get("lockQueue")
        self.meta_description = data.get("metaDescription")
        self.welcome_message = data.get("welcomeMessage")
        self.now_playing = data.get("currentSong")
        self.slow_mode = data.get("slowMode")

        self.room_id = "room:" + self.id
        self.members = MemberCollection()
        self.playlist = RoomPlaylist(current_song=data.get("currentSong"))

    async def change_presence(self, presence: Presence):
        await self.client.socket.send(action=Actions.presence_change, channel=self.room_id, presence=
                                      PresenceChange(presence, self.client.user.id, self.client.connection_id))

    async def send_message(self, text: str):
        from . import Message
        _, raw = await self.client.http.post(Endpoints.chat(rid=self.id), data={
            "type": "chat-message",
            "realTimeChannel": self.rtc,
            "time": utils.ts(datetime.utcnow()),
            "message": text
        })

        raw.update(raw['req'])
        return Message(self.client, raw)

class RoomDisplaySettings:
    def __init__(self, data: dict):
        self.queue = data.get("displayQueue")
        self.in_search = data.get("displayInSearch")
        self.in_lobby = data.get("displayInLobby")
        self.dj_in_queue = data.get("displayDJinQueue")
        self.user_join = data.get("displayUserJoin")
        self.user_leave = data.get("displayUserLeave")
        self.user_grab = data.get("displayUserGrab")

class RoomPlaylist(list):
    def __init__(self, current_song=None):
        super().__init__()
        self.now_playing = current_song

    def next_song(self):
        self.now_playing = self.pop(0)

class RoomCollection(Collection):
    def from_rtc(self, rtc):
        return utils.get(self.values(), rtc=rtc)

    def from_room_id(self, room_id: str):
        _, rid = room_id.split(":")
        return self.get(rid, None)

class PresenceChange:
    def __init__(self, presence: Presence, client_id: str, connection_id: str):
        self.action = presence.value
        self.clientId = client_id
        self.connectionId = connection_id
        self.data = {}
