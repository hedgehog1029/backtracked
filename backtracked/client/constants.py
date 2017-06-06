import urllib.parse

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
