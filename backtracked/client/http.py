import aiohttp
import asyncio
from .. import __version__
from . import constants
from ..models.errors import *

import logging

class ProxyOptions:
    """
    Used to pass proxy options to the HTTP and WebSocket clients.
    
    .. _ClientSession: http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession
    .. _aiosocks: https://github.com/nibrag/aiosocks
    
    Parameters
    ----------
    proxy_url: str
        Proxy URL used by `aiohttp`_. Certain connectors will use this option.
    client_request: :class:`aiohttp.ClientRequest`
        Custom `ClientRequest`, if needed for your proxy solution.
        
    Examples
    --------

    `aiosocks`_ socks4 proxy example:

    .. code-block:: python

        from backtracked import Client, ProxyOptions
        from aiosocks import connector

        proxy_opts = ProxyOptions("socks4://127.0.0.1:1080", client_request=connector.ProxyClientRequest)
        c = Client(connector=connector.ProxyConnector(), proxy_options=proxy_opts)

        @c.event
        async def on_ready():
            print("Logged in as {0.username}".format(c.user))

        c.run("email", "password")
    """
    def __init__(self, proxy_url: str, client_request: aiohttp.ClientRequest=None):
        self.proxy = proxy_url
        self.client_request = client_request if client_request is not None else aiohttp.ClientRequest

# TODO: Ratelimiting, once the dubtrack API makes sense
class HTTPClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, connector=None, proxy_options: ProxyOptions=None):
        user_agent = "backtracked/{0}".format(__version__)
        headers = {"User-Agent": user_agent}
        default_connector = aiohttp.TCPConnector(verify_ssl=True)

        self.log = logging.getLogger("backtracked.http")
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
        self.log.debug("{method} {path}: {0.status}".format(r, method=method, path=path))

        if r.status == 200:
            j = await r.json()
            # TODO: why did I return status here. bad ideas
            return 200, j["data"]
        else:
            # TODO: ok so the error handling needs improvement
            raise ApiError(path, r.status, "Server returned error")

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)
