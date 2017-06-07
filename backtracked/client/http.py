import aiohttp
import asyncio
from .. import __version__
from . import constants

class ProxyOptions:
    def __init__(self, proxy_url: str, client_request: aiohttp.ClientRequest=None):
        self.proxy = proxy_url
        self.client_request = client_request if client_request is not None else aiohttp.ClientRequest

# TODO: Ratelimiting, once the dubtrack API makes sense
class HTTPClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, connector=None, proxy_options: ProxyOptions=None):
        user_agent = "backtracked/{0}".format(__version__)
        headers = {"User-Agent": user_agent}
        default_connector = aiohttp.TCPConnector(verify_ssl=True)

        self.loop = loop
        self.connector = default_connector if connector is None else connector
        self.proxy_options = ProxyOptions(None) if proxy_options is None else proxy_options
        self.session = aiohttp.ClientSession(connector=self.connector, loop=loop, headers=headers,
                                             request_class=self.proxy_options.client_request)

    async def request(self, method, path: str, **kwargs):
        url = (constants.base_url + path)

        if self.proxy_options.proxy is not None:
            kwargs["proxy"] = self.proxy_options.proxy

        r = await self.session.request(method, url, **kwargs)
        print("{method} {path}: {0.status}".format(r, method=method, path=path))

        if r.status == 200:
            j = await r.json()
            return j["data"]

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)
