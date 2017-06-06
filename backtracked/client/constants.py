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
    joinRoom = 10
    joinedRoom = 11
    leaveRoom = 12
    leftRoom = 13
    presenceChange = 14
    roomAction = 15

class Events:
    # main
    on_ready = "on_ready"
    on_joined_room = "on_joined_room"
    on_chat = "on_chat"

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
