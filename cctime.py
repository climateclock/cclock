"""Time-handling functions that work in both Python and CircuitPython."""

import utils

utils.mem('cctime1')
import time
utils.mem('cctime2')
try:
    import datetime
    utils.mem('cctime3')
except:
    import adafruit_datetime as datetime
    utils.mem('cctime4')

EPOCH = datetime.datetime(1970, 1, 1)
fake_time = None
time_source = None


def monotonic():
    """Returns a monotonically increasing floating-point number of seconds."""
    if fake_time:
        return fake_time
    return time.monotonic()


def enable_rtc():
    """Activates use of an attached DS3231 RTC as the time source."""
    global time_source
    try:
        import board
        import rtc
    except:
        print(f'No rtc module available; using internal clock')
        return
    try:
        from adafruit_ds3231 import DS3231
        time_source = DS3231(board.I2C())
        rtc.set_time_source(time_source)
    except Exception as e:
        utils.report_error(e, 'Could not find an attached DS3231 RTC')


def set_rtc(y, l, d, h, m, s):
    """Sets the time on the attached RTC, if enabled."""
    if time_source:
        time_source.datetime = time.struct_time((y, l, d, h, m, s, 0, -1, -1))


def monotonic():
    """Returns a monotonically increasing floating-point number of seconds."""
    if fake_time:
        return fake_time
    return time.monotonic()


def get_time():
    """Returns the current time in seconds since 1970-01-01 00:00:00 UTC."""
    if fake_time:
        return fake_time
    return time.time()


def get_datetime():
    """Returns the current time as a datetime in UTC."""
    if hasattr(time, 'gmtime'):
        return datetime.datetime.utcfromtimestamp(get_time())
    else:
        # In CircuitPython, time.gmtime and datetime.utcfromtimestamp are
        # missing; there are no time zones and all datetimes are in UTC.
        return datetime.datetime.fromtimestamp(get_time())


def set_fake_time(t):
    """Sets the time for testing.  To use the real time, set_fake_time(None)."""
    global fake_time
    fake_time = t


def sleep(t):
    """Advances the time by the given amount, sleeping if necessary."""
    if fake_time:
        set_fake_time(fake_time + t)
    else:
        time.sleep(t)


def wait_until(t):
    """Advances the time to the given time or later, sleeping if necessary."""
    if fake_time:
        set_fake_time(t)
        return t
    else:
        now = get_time()
        if t > now:
            time.sleep(t - now)
        return now


def isoformat_to_datetime(s):
    """Parses a string in the form yyyy-mm-ddThh:mm:ss into a datetime."""
    return datetime.datetime.fromisoformat(s[:19])  # ignore time zone offset


def isoformat_to_date(s):
    """Parses a string in the form yyyy-mm-ddThh:mm:ss into a date."""
    return isoformat_to_datetime(s).date()


utils.mem('cctime5')


class FrameTimer:
    def __init__(self, fps):
        self.next = 0
        self.interval = 1/fps

    def wait(self):
        """Waits until the next frame display time."""
        self.next = wait_until(self.next) + self.interval


utils.mem('cctime6')
