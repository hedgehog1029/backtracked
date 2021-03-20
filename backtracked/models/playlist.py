from .base import Model
from .. import utils

__all__ = ["Song", "SongInfo"]

class Song(Model):
    """
    Represents a song on QueUp that will play, is playing, or has played in the past.

    Attributes
    ----------
    id: str
        ID of this song entry
    created_at: :class:`datetime.datetime`
        Datetime representing the time this song was added.
    played_at: :class:`datetime.datetime`
        Datetime representing the time this song was played.
    active: bool
        True if this song is currently playing, False otherwise
    played: bool
        True if this song was played in the past, False otherwise
    skipped: bool
        True if this song was skipped, False otherwise.
    order: int
        Order of this song
    length: int
        Length of this song's assigned media in milliseconds. You can use :meth:`backtracked.utils.song_length` to
        convert this to a human-readable string.
    up_dubs: int
        Number of updubs this song has received.
    down_dubs: int
        Number of downdubs this song has received.
    """
    def __init__(self, client, data: dict):
        super().__init__(client)
        self.id = data.get("_id")
        self.created_at = utils.dt(data.get("created"))
        self.played_at = utils.dt(data.get("played"))
        self.active = data.get("isActive")
        self.played = data.get("isPlayed")
        self.skipped = data.get("skipped")
        self.order = data.get("order")
        self.length = data.get("songLength")
        self.up_dubs = data.get("updubs")
        self.down_dubs = data.get("downdubs")

        self._roomid = data.get("roomid")
        self._userid = data.get("userid")
        self._songid = data.get("songid")

    @property
    def room(self):
        """
        Get the room this playlist entry was added to.

        Returns
        -------
        :class:`Room`
            Room this song exists in.
        """
        return self.client.rooms.get(self._roomid)

    @property
    def user(self):
        """
        Get the user who added this playlist entry.

        Returns
        -------
        :class:`User`
            User who added this playlist entry.
        """
        return self.client.users.get(self._userid)

    @property
    def song_info(self):
        """
        Get the media information object for this song.

        Returns
        -------
        :class:`SongInfo`
            Media information object for this playlist entry.
        """
        return self.client.song_cache.get(self._songid)

    @property
    def net_dubs(self):
        """
        Total number of dubs this song has received.

        Returns
        -------
        int
            Net number of dubs
        """
        return self.up_dubs - self.down_dubs

class SongInfo:
    """
    Represents a specific media from a specific media source.

    Attributes
    ----------
    id: str
        QueUp ID of this media object.
    name: str
        Source-provided name of this media object.
    media_id: str
        Source's ID for this media object.
    source: str
        Name of the source that provided this media object.
    created_at: :class:`datetime.datetime`
        Datetime representing the time this media was created at the source.
    length: int
        Length of this media in milliseconds. You can use :meth:`backtracked.utils.song_length` to
        convert this to a human-readable string.
    thumbnail: str
        URL of the thumbnail for this media.
    """
    def __init__(self, data: dict):
        self.id = data.get("_id")
        self.name = data.get("name")
        self.source = data.get("type")
        self.created_at = utils.tzdt(data.get("created"))
        self.length = data.get("songLength")
        self.media_id = data.get("fkid")
        self.thumbnail = data.get("images", {}).get("thumbnail")
