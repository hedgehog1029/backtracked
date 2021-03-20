from enum import Enum

def fmt(input: str):
    def format(*args, **kwargs):
        return input.format(*args, **kwargs)
    return format

def ws_url(token: str):
    return "wss://ws.queup.net/ws/?connect=1&access_token={token}&EIO=3&transport=websocket"\
            .format(token=token)

base_url = "https://api.queup.net"

class Endpoints:
    auth_dubtrack = "/auth/login"
    auth_session = "/auth/session"
    auth_token = "/auth/token"
    chat = fmt("/chat/{rid}")
    chat_ban = fmt("/chat/ban/{rid}/user/{uid}")
    conversations = "/message"
    conversations_new = "/message/new"
    conversation = fmt("/message/{cid}")
    conversation_read = fmt("/message/{cid}/read")
    room_join = fmt("/room/{slug}")
    room_users = fmt("/room/{rid}/users")
    member_set_role = fmt("/chat/{roleid}/{rid}/user/{uid}")
    user_update_username = "/user/updateUsername"

class Actions(Enum):
    heartbeat = 0
    ack = 1
    nack = 2
    connect = 3
    connected = 4
    disconnect = 5
    disconnected = 6
    close = 7
    closed = 8
    error = 9
    join_room = 10
    joined_room = 11
    leave_room = 12
    left_room = 13
    presence_change = 14
    room_action = 15
    sync = 16
    token = 17

class RoomActions(Enum):
    chat_message = "chat-message"
    chat_skip = "chat-skip"
    chat_delete = "delete-chat-message"
    room_playlist_dub = "room_playlist-dub"
    room_playlist_grab = "room_playlist-queue-update-grabs"
    room_playlist_update_dubs = "room_playlist-queue-update-dub"
    room_playlist_update = "room_playlist-update"
    room_update = "room-update"
    user_ban = "user-ban"
    user_image_update = "user-update"
    user_join = "user-join"
    user_kick = "user-kick"
    user_leave = "user-leave"
    user_mute = "user-mute"
    user_set_role = "user-setrole"
    user_unban = "user-unban"
    user_unmute = "user-unmute"
    user_unset_role = "user-unsetrole"
    user_update = "user_update"
    room_pause_queue = "user-pause-queue"

    new_message = "new-message"

    dynamic = "*"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

class Events:
    # main
    on_ready = "on_ready"
    on_joined_room = "on_joined_room"
    on_chat = "on_chat"
    on_chat_skip = "on_chat_skip"
    on_chat_delete = "on_chat_delete"
    on_member_join = "on_member_join"
    on_member_presence = "on_member_presence"
    on_member_update = "on_member_update"
    on_playlist_song_add = "on_playlist_song_add"
    on_dub = "on_dub"
    on_private_message = "on_private_message"

    # aliases
    on_message = on_chat

class RoleGlobal:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.type = kwargs.get("type")
        self.label = kwargs.get("label")
        self.rights = kwargs.get("rights", [])

# Public
__all__ = ["Presence", "Role"]

class Presence(Enum):
    """
    Represents a member's presence in a room.
    
    Attributes
    ----------
    enter:
        "Visible" presence
    exit:
        "Invisible" presence
    """
    enter = 0
    exit = 1
    update = 2

    join = enter
    leave = exit

# Possibly have a Rights enum
class Role(Enum):
    """
    Represents a possible role that may be assigned to a member.
    
    Attributes
    ----------
    resident_dj:
        Resident DJ role.
    vip:
        VIP role.
    moderator:
        Moderator role (can kick+ban)
    manager:
        Manager role
    co_owner:
        Co-Owner role
    """
    resident_dj = RoleGlobal(id="5615feb8e596154fc2000002", type="resident-dj", label="Resident DJ", rights=["set-dj"])
    vip = RoleGlobal(id="5615fe1ee596154fc2000001", type="vip", label="VIP", rights=["skip", "set-dj"])
    moderator = RoleGlobal(id="52d1ce33c38a06510c000001", type="mod", label="Moderator", rights=["skip", "queue-order",
                           "kick", "ban", "mute", "set-dj", "lock-queue", "delete-chat", "chat-mention"])
    manager = RoleGlobal(id="5615fd84e596150061000003", type="manager", label="Manager", rights=["skip", "queue-order",
                         "kick", "ban", "mute", "set-dj", "lock-queue", "delete-chat", "chat-mention", "set-roles"])
    co_owner = RoleGlobal(id="5615fa9ae596154a5c000000", type="co-owner", label="Co-Owner", rights=["skip",
                          "queue-order", "kick", "ban", "mute", "set-dj", "lock-queue", "delete-chat", "chat-mention",
                          "set-roles", "update-room", "set-managers"])

    _role_map = {
        "5615feb8e596154fc2000002": resident_dj,
        "5615fe1ee596154fc2000001": vip,
        "52d1ce33c38a06510c000001": moderator,
        "5615fd84e596150061000003": manager,
        "5615fa9ae596154a5c000000": co_owner
    }

    @classmethod
    def from_id(cls, role_id: str):
        return cls._role_map.get(role_id)
