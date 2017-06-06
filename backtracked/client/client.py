from .http import HTTPClient
from .constants import Endpoints
from .socket import SocketClient
import asyncio

class Client:
    def __init__(self, **kwargs):
        self.loop = asyncio.get_event_loop()
        self.http = HTTPClient(self.loop, connector=kwargs.get("connector", None))
        self.user = None

        self._socket = SocketClient(self.http)

    async def login(self, email: str, password: str):
        await self.http.post(Endpoints.auth_dubtrack, data={"username": email, "password": password})
        user_raw = await self.http.get(Endpoints.auth_session)
        print(user_raw)

    async def connect(self):
        resp = await self.http.get(Endpoints.auth_token)
        await self._socket.connect(resp["token"])

    def run(self, email, password):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.login(email, password))
            loop.run_until_complete(self.connect())
        except KeyboardInterrupt:
            self.close()
            pending = asyncio.Task.all_tasks(loop=self.loop)
            gathered = asyncio.gather(*pending, loop=self.loop)

            try:
                gathered.cancel()
                self.loop.run_until_complete(gathered)
                gathered.exception()
            except:
                pass
        finally:
            self.loop.close()

    def close(self):
        self.http.session.close()
