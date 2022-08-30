"""Time-handling functions that work in both Python and CircuitPython."""

try:
    import adafruit_datetime as datetime
except:
    datetime = __import__('datetime')
import time
import utils

EPOCH = datetime.datetime(1970, 1, 1)
fake_millis = None
ref_millis = None
time_source = None


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


def get_millis():
    """Returns the current time in milliseconds since 1970-01-01 00:00 UTC."""
    if fake_millis:
        return fake_millis
    global ref_millis
    if not ref_millis:
        ref_millis = int(time.time() * 1000) - int(time.monotonic() * 1000)
    return ref_millis + int(time.monotonic() * 1000)


def get_datetime():
    """Returns the current time as a datetime in UTC."""
    return millis_to_datetime(get_millis())


def millis_to_datetime(ms):
    if datetime.__name__ == 'datetime':
        return datetime.datetime.utcfromtimestamp(ms//1000)
    else:
        # In CircuitPython, time.gmtime and datetime.utcfromtimestamp are
        # missing; there are no time zones and all datetimes are in UTC.
        return datetime.datetime.fromtimestamp(ms//1000)


def datetime_to_millis(dt):
    return int((dt - EPOCH).total_seconds() * 1000)


def set_fake_millis(ms):
    """Sets the time for testing.  To use the real time, set_fake_millis(None)."""
    global fake_millis
    fake_millis = ms


def sleep_millis(ms):
    """Advances the time by the given amount, sleeping if necessary."""
    if fake_millis:
        set_fake_millis(fake_millis + ms)
    else:
        time.sleep(ms/1000)


def wait_until_millis(ms):
    """Advances the time to the given time or later, sleeping if necessary."""
    if fake_millis:
        set_fake_millis(ms)
    else:
        now = get_millis()
        if ms > now:
            time.sleep(ms - now)


def isoformat_to_datetime(s):
    """Parses a string in the form yyyy-mm-ddThh:mm:ss into a datetime."""
    return datetime.datetime.fromisoformat(s[:19])  # ignore time zone offset


def try_isoformat_to_millis(data, key):
    value = data.get(key)
    try:
        return datetime_to_millis(isoformat_to_datetime(value))
    except Exception as e:
        print('Invalid timestamp for %r: %r' % (key, value))
