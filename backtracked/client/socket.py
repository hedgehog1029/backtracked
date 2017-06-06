from .engine.packets import Packet, PacketType
from .http import HTTPClient
from . import constants
import aiohttp
import asyncio

# TODO: Proper configurable logging rather than print
class SocketClient:
    def __init__(self, http: HTTPClient):
        self.loop = http.loop
        self.session = http.session
        self.ws = None

        # Ping
        self.ping_interval = 0
        self.ping_timeout = 0
        self.interval_timer = None
        self.timeout_timer = None

    async def connect(self, token: str):
        print("ws connect")
        self.ws = await self.session.ws_connect(constants.ws_url(token))
        print("connected")

        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT or msg.type == aiohttp.WSMsgType.BINARY:
                packet = Packet.decode(msg.data)
                await self._handle(packet)

    async def _handle(self, packet: Packet):
        print("WS Recv: [{0.type.name}] {0.data}".format(packet))

        if packet.type == PacketType.OPEN:
            j = packet.to_json()
            self.ping_interval = int(j["pingInterval"] / 1000)
            self.ping_timeout = int(j["pingTimeout"] / 1000)

            self._setPingInterval()
        elif packet.type == PacketType.CLOSE:
            print("WebSocket closed")
        elif packet.type == PacketType.PONG:
            self._setPingInterval()
        elif packet.type == PacketType.MESSAGE:
            self._setPingTimeout()
            print(packet.to_json())

    def _setPingInterval(self):
        if self.interval_timer is not None:
            self.interval_timer.cancel()

        async def interval():
            await asyncio.sleep(self.ping_interval)
            await self._ping()
            self._setPingInterval()

        self.interval_timer = self.loop.create_task(interval())

    def _setPingTimeout(self, ping_timeout=0):
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()

        async def timeout(timeout):
            await asyncio.sleep(timeout)
            await self.ws.close()

        tout = ping_timeout if ping_timeout > 0 else self.ping_timeout+self.ping_interval
        self.timeout_timer = self.loop.create_task(timeout(tout))

    async def _ping(self):
        await self.ws.send_bytes(Packet(PacketType.PING).encode())
        self._setPingTimeout(self.ping_timeout)
