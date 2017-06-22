import asyncio
import aiohttp

from . import constants
from .engine.packets import Packet, PacketType

import json
import logging

class SocketClient:
    def __init__(self, client):
        self.log = logging.getLogger("backtracked.socket")
        self._client = client
        self.loop = client.http.loop
        self.session = client.http.session
        self.ws = None

        # Ping
        self.ping_interval = 0
        self.ping_timeout = 0
        self.interval_timer = None
        self.timeout_timer = None

    async def connect(self, token: str):
        opts = {}

        if self._client.http.proxy_options.proxy is not None:
            opts["proxy"] = self._client.http.proxy_options.proxy

        self.log.debug("WebSocket attempting to connect...")
        self.ws = await self.session.ws_connect(constants.ws_url(token), **opts)
        self.log.debug("WebSocket connected.")

        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT or msg.type == aiohttp.WSMsgType.BINARY:
                packet = Packet.decode(msg.data)
                await self._handle(packet)
            else:
                print(msg.type)
                print(msg.data)

        self.log.warning("Websocket was closed: {0}".format(self.ws.exception()))

    async def _handle(self, packet: Packet):
        # print("WS Recv: [{0.type.name}] {0.data}".format(packet))

        if packet.type == PacketType.OPEN:
            j = packet.to_dict()
            self.ping_interval = int(j["pingInterval"] / 1000)
            self.ping_timeout = int(j["pingTimeout"] / 1000)

            self._setPingInterval()
        elif packet.type == PacketType.CLOSE:
            self.log.warning("WebSocket closed.")
        elif packet.type == PacketType.PONG:
            self._setPingInterval()
        elif packet.type == PacketType.MESSAGE:
            self._setPingTimeout()

            msg = DubtrackMessage(packet.to_dict())
            try:
                self._client._handle_payload(msg)
            except BaseException as exc:
                self.log.exception("There was an error processing a websocket payload:\n{0}".format(msg.action.name))

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

    def send(self, **kwargs):
        kwargs["action"] = kwargs.get("action", constants.Actions.heartbeat).value
        return self._send(kwargs)

    async def _send(self, payload: dict):
        packet = Packet(PacketType.MESSAGE, data_json=payload)
        await self.ws.send_str(packet.encode_str())
        self.log.debug("WS Send: {0.type.name} - {0.data}".format(packet))

class AttributeProxy:
    def __init__(self, data: dict):
        self.data = data

    def __getattr__(self, name: str):
        return self.data.get(name, None)

    def __getitem__(self, item):
        return self.data.get(item, None)

class DubtrackMessage(AttributeProxy):
    def __init__(self, payload: dict):
        super().__init__(payload)
        self.action = constants.Actions(payload.get("action"))

class RoomActionMessage:
    def __init__(self, message: dict):
        self.name = constants.RoomActions(message.get("name"))
        self.type = message.get("type")

        if self.type == "json":
            self.value = AttributeProxy(json.loads(message.get("data")))
