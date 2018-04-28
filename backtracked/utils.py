from collections import Iterable
from datetime import datetime

__all__ = ["get", "song_length", "dt", "ts", "tzdt"]

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

    Parameters
    ----------
    iterable: :class:`Iterable`
        Iterable of objects to check
    attrs: kwargs
        Key-value pairs of attributes to check against

    Returns
    -------
    object:
        First element in the iterable that has all the required attributes
    """
    for item in iterable:
        if all(valid(item, attrs)):
            return item
    return None

def song_length(length: int, format="%M:%S"):
    """
    Convert a song length in milliseconds to a human-readable format, e.g. `03:54`.

    Parameters
    ----------
    length: int
        Length in milliseconds to convert
    format: str
        Optional custom format, to change the output. Passed to :meth:`datetime.datetime.strftime`.

    Returns
    -------
    str:
        String representing the length of time according to the format string.
    """
    return dt(length).strftime(format)

def dt(msts: int) -> datetime:
    """
    Converts a JavaScript-style timestamp (milliseconds) to a Python datetime.

    Parameters
    ----------
    msts: int
        Timestamp to convert

    Returns
    -------
    :class:`datetime.datetime`
        Python datetime representing the passed date
    """
    return datetime.fromtimestamp(float(msts) / 1000)

def ts(time: datetime) -> float:
    """
    Converts a Python datetime to a JavaScript-style timestamp (milliseconds). Not 100% accurate.

    Parameters
    ----------
    time: :class:`datetime.datetime`
        Datetime to convert.

    Returns
    -------
    float:
        Number of milliseconds elapsed since 1970.
    """
    return time.timestamp() * 1000

def tzdt(fulldate: str):
    """
    Converts an ISO 8601 full timestamp to a Python datetime.

    Parameters
    ----------
    fulldate: str
        ISO 8601 UTC timestamp, e.g. `2017-06-02T16:23:14.815Z`

    Returns
    -------
    :class:`datetime.datetime`
        Python datetime representing ISO timestamp.
    """
    if fulldate[-1] == "Z":
        fulldate = fulldate[0:-1] + "+0000"

    return datetime.strptime(fulldate, "%Y-%m-%dT%H:%M:%S.%f%z")
