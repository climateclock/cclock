"""Time-handling functions, including a clock that can be faked for testing.

Times are represented as float seconds since 1970-01-01 00:00:00 UTC.
"""

import datetime

EPOCH = datetime.datetime(1970, 1, 1)
fake_time = None


def get_time():
    """Returns the current time in seconds since 1970-01-01 00:00:00 UTc."""
    if fake_time:
        return fake_time
    import time

    return time.time()


def set_fake_time(t):
    """Sets the time for testing.  To use the real time, set_fake_time(None)."""
    global fake_time
    fake_time = t


def isoformat_to_datetime(s):
    return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")


def isoformat_to_date(s):
    return isoformat_to_datetime(s).date()


def isoformat_to_time(s):
    return (isoformat_to_datetime(s) - EPOCH).total_seconds()
