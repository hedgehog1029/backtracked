from collections import Iterable
from datetime import datetime

__all__ = ["get", "dt", "ts"]

def valid(item, attrs: dict):
    for name, value in attrs.items():
        if hasattr(item, name):
            if getattr(item, name) != value:
                yield False
            else:
                yield True
        else:
            yield False

def get(iterable: Iterable, **attrs):
    """
    Finds the first object in an iterable that has all attributes present and equal to their value
    :param iterable: Iterable of objects to check
    :param attrs: Key-value pairs of attributes to check against
    :return: First element in the iterable that has all the required attributes
    """
    for item in iterable:
        if all(valid(item, attrs)):
            return item
    return None

def dt(msts: int) -> datetime:
    return datetime.fromtimestamp(float(msts) / 1000)

def ts(time: datetime) -> float:
    return time.timestamp() * 1000
