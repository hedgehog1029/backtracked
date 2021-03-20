import asyncio
import aiohttp

from . import constants
from .engine.packets import Packet, PacketType

import json
import logging

log = logging.getLogger("backtracked.socket")

def cleaner(future: asyncio.Future):
    try:
        future.exception()
    except (asyncio.CancelledError, asyncio.InvalidStateError):
        pass

class SocketClient:
    def __init__(self, client):
        self._client = client
        self.loop = client.http.loop
        self.session = client.http.session
        self.ws = None

        # Ping
        self.ping_interval = 0
        self.ping_timeout = 0
        self.interval_timer = None
        self.timeout_timer = None
        self.should_reconnect = True

    async def connect(self, token: str):
        """Connect to the websocket until closed."""

        while self.should_reconnect:
            await self._connect(token)

    async def _connect(self, token: str):
        opts = {}

        if self._client.http.proxy_options.proxy is not None:
            opts["proxy"] = self._client.http.proxy_options.proxy

        log.debug("WebSocket attempting to connect...")
        self.ws = await self.session.ws_connect(constants.ws_url(token), **opts)
        log.debug("WebSocket connected.")

        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT or msg.type == aiohttp.WSMsgType.BINARY:
                packet = Packet.decode(msg.data)
                await self._handle(packet)
            else:
                log.debug(msg.type)
                log.debug(msg.data)

        # TODO: Reconnect, I guess
        log.warning("Websocket was closed: {0}".format(self.ws.exception()))

    async def _handle(self, packet: Packet):
        # log.debug("Raw recv: [{0.type.name}] {0.data}".format(packet))

        if packet.type == PacketType.OPEN:
            j = packet.to_dict()
            self.ping_interval = int(j["pingInterval"] / 1000)
            self.ping_timeout = int(j["pingTimeout"] / 1000)

            self._set_ping_interval()
        elif packet.type == PacketType.CLOSE:
            log.warning("WebSocket closed.")
        elif packet.type == PacketType.PONG:
            # Clear ping timeout, we got a pong
            self._clear_ping_timeout()
            # Wait ping interval before sending a ping again
            self._set_ping_interval()
        elif packet.type == PacketType.MESSAGE:
            msg = QueUpMessage(packet.to_dict())
            try:
                self._client._handle_payload(msg)
            except BaseException as exc:
                log.exception("There was an error processing a websocket payload:\n{0}".format(msg.action.name))

    # Ping behaviour documentation: https://github.com/socketio/engine.io-protocol/tree/v3#timeouts
    def _set_ping_interval(self):
        if self.interval_timer is not None:
            self.interval_timer.cancel()

        async def interval():
            await asyncio.sleep(self.ping_interval)
            await self._ping()

        self.interval_timer = self.loop.create_task(interval())
        self.interval_timer.add_done_callback(cleaner)

    def _clear_ping_timeout(self):
        if self.timeout_timer is not None:
            self.timeout_timer.cancel()

    def _set_ping_timeout(self, ping_timeout=0):
        self._clear_ping_timeout()

        async def timeout(timeout):
            await asyncio.sleep(timeout)
            log.debug("Ping response timed out")
            await self.ws.close()

        self.timeout_timer = self.loop.create_task(timeout(ping_timeout))
        self.timeout_timer.add_done_callback(cleaner)

    async def _ping(self):
        await self.ws.send_str(Packet(PacketType.PING).encode_str())
        self._set_ping_timeout(self.ping_timeout)

    def send(self, **kwargs):
        kwargs["action"] = kwargs.get("action", constants.Actions.heartbeat).value
        return self._send(kwargs)

    async def _send(self, payload: dict):
        packet = Packet(PacketType.MESSAGE, data_json=payload)
        await self.ws.send_str(packet.encode_str())
        log.debug("WS Send: {0.type.name} - {0.data}".format(packet))

class AttributeProxy:
    def __init__(self, data: dict):
        self.data = data

    def __getattr__(self, name: str):
        return self.data.get(name, None)

    def __getitem__(self, item):
        return self.data.get(item, None)

class QueUpMessage(AttributeProxy):
    def __init__(self, payload: dict):
        super().__init__(payload)
        self.action = constants.Actions(payload.get("action"))

class RoomActionMessage:
    def __init__(self, message: dict):
        if constants.RoomActions.has_value(message.get("name")):
            self.name = constants.RoomActions(message.get("name"))
        elif message.get("name").startswith("user_update_"):
            self.name = constants.RoomActions.user_update
        else:
            self.name = constants.RoomActions.dynamic

        self.type = message.get("type")

        if self.type == "json":
            self.value = AttributeProxy(json.loads(message.get("data")))
