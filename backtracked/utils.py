from collections import Iterable
from datetime import datetime

def get(iterable: Iterable, **attrs):
    for item in iterable:
        for name, value in attrs.items():
            if hasattr(item, name):
                if getattr(item, name) == value:
                    return item
    return None

def dt(msts: int) -> datetime:
    return datetime.fromtimestamp(msts / 1000)

def ts(time: datetime) -> float:
    return time.timestamp() * 1000
