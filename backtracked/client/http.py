import aiohttp
import asyncio
from .. import __version__
from . import constants

from aiosocks.connector import ProxyClientRequest

# TODO: Ratelimiting, once the dubtrack API makes sense
class HTTPClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, connector=None):
        user_agent = "backtracked/{0}".format(__version__)
        headers = {"User-Agent": user_agent}
        default_connector = aiohttp.TCPConnector(verify_ssl=True)

        self.connector = default_connector if connector is None else connector
        self.loop = loop
        self.session = aiohttp.ClientSession(connector=self.connector, loop=loop, headers=headers)

    async def request(self, method, path: str, **kwargs):
        url = (constants.base_url + path)

        r = await self.session.request(method, url, **kwargs)
        print("{method} {path}: {0.status}".format(r, method=method, path=path))

        if r.status == 200:
            j = await r.json()
            return j["data"]

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)
