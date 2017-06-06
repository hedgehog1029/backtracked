from enum import Enum
import six
import json
import base64

__all__ = ["PacketType", "Packet"]

# Engine.IO packet tools
class PacketType(Enum):
    OPEN = 0
    CLOSE = 1
    PING = 2
    PONG = 3
    MESSAGE = 4
    UPGRADE = 5
    NOOP = 6

class Packet:
    default_encoding = "utf-8"

    def __init__(self, packet_type: PacketType = PacketType.NOOP, data: bytes = None, data_json=None):
        self.type = packet_type

        if data_json is not None:
            data = json.dumps(data_json, default=lambda o: o.__dict__)

        if data is not None:
            if isinstance(data, str):
                self.data = bytes(data, encoding=self.default_encoding)
            else:
                self.data = bytes(data)
        else:
            self.data = None

    def to_dict(self):
        return json.loads(self.data)

    def encode(self) -> bytes:
        type = bytes(str(self.type.value), encoding=self.default_encoding)

        if self.data is not None:
            return type + self.data
        else:
            return type

    def encode_str(self):
        type = str(self.type.value)

        if self.data is not None:
            data = self.data.decode(self.default_encoding)
            return type + data
        else:
            return type

    @classmethod
    def decode(cls, packet: str):
        packet = bytes(packet, encoding=cls.default_encoding)
        packet_type = six.byte2int(packet[:1])

        if packet_type == 98:  # b64 flag
            part = packet[1:]
            dec_type = PacketType(six.byte2int(part[:1]))
            decoded = base64.b64decode(part[1:])

            return cls(dec_type, decoded)
        packet_type -= 48  # string encoded numbers bois

        dec_type = PacketType(packet_type)
        if len(packet) > 1:
            data = packet[1:]

            return cls(dec_type, data)
        else:
            return cls(dec_type)
