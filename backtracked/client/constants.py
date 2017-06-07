from enum import Enum

def fmt(input: str):
    def format(*args, **kwargs):
        return input.format(*args, **kwargs)
    return format

def ws_url(token: str):
    return "wss://ws.dubtrack.fm/ws/?connect=1&access_token={token}&EIO=3&transport=websocket"\
            .format(token=token)

base_url = "https://api.dubtrack.fm"

class Endpoints:
    auth_dubtrack = "/auth/dubtrack"
    auth_session = "/auth/session"
    auth_token = "/auth/token"
    chat = fmt("/chat/{rid}")
    chat_ban = fmt("/chat/ban/{rid}/user/{uid}")
    room_join = fmt("/room/{slug}")
    room_users = fmt("/room/{rid}/users")

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

class RoomActions(Enum):
    chat_message = "chat-message"
    chat_skip = "chat-skip"
    chat_delete = "delete-chat-message"
    room_playlist_dub = "room_playlist-dub"
    room_playlist_grab = "room_playlist-queue-update-grabs"
    room_playlist_update_dubs = "room_playlist-queue-update-dub"
    room_playlist_update = "room_playlist"
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

class Events:
    # main
    on_ready = "on_ready"
    on_joined_room = "on_joined_room"
    on_chat = "on_chat"
    on_chat_skip = "on_chat_skip"
    on_chat_delete = "on_chat_delete"
    on_member_join = "on_member_join"

    # aliases
    on_message = on_chat

# Public
__all__ = ["Presence"]

class Presence(Enum):
    enter = 0
    exit = 1
    update = 2

    join = enter
    leave = exit
