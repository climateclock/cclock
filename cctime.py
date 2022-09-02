"""Time-handling functions that work in both Python and CircuitPython."""

import time
import utils

# Offset of Unix epoch (1970-01-01) from NTP epoch (1900-01-01), in seconds
NTP_OFFSET = 2208988800

# CircuitPython cannot perform time calculations before 2000
MIN_MILLIS = 946684800_000  # 2000-01-01 00:00:00 UTC represented as Unix time

# Unix time in ms that corresponds to monotonic_ns() == 0
ref_millis = MIN_MILLIS  # the board starts up with the clock set to 2000-01-01
rtc_source = None


def get_millis():
    return ref_millis + time.monotonic_ns()//1000000


def set_millis(millis):
    global ref_millis
    print('Setting cctime clock to', millis_to_isoformat(millis))
    ref_ns = time.monotonic_ns()
    ref_millis = millis - ref_ns//1000000
    if rtc_source:
        # TODO: To set the RTC with sub-second precision, try waiting
        # until the transition to the next second to set the RTC.
        tm = time.localtime(millis//1000)
        print('Setting RTC to', tm)
        rtc_source.datetime = tm


def enable_rtc():
    # Activates use of an attached DS3231 RTC as the time source.
    global ref_millis, rtc_source
    try:
        import board
        import rtc
    except:
        print(f'No rtc module available; using internal clock')
        return
    try:
        from adafruit_ds3231 import DS3231
        rtc_source = DS3231(board.I2C())
        rtc_datetime, ref_ns = rtc_source.datetime, time.monotonic_ns()
        # TODO: To get sub-second precision from the RTC, try sampling it
        # until we detect a transition to the next second.
        ref_millis = time.mktime(rtc_datetime)*1000 - ref_ns//1000000
    except Exception as e:
        rtc_source = None
        utils.report_error(e, 'Could not find an attached DS3231 RTC')


def ntp_sync(socket, server):
    # Gets the time from an NTP server and sets the clock accordingly.
    s = socket.socket(type=socket.SOCK_DGRAM)
    try:
        addr = socket.getaddrinfo(server, 123)[0][4]
        s.connect(addr, conntype=1)  # esp.UDP_MODE == 1
        packet = bytearray(48)
        packet[0] = 0b_00_100_011  # no leap second, NTP version 4, client mode
        s.settimeout(0.5)
        s.send(packet)
        if s.recv_into(packet) == 48:
            ntp_time = ((packet[40] << 24) + (packet[41] << 16) +
                (packet[42] << 8) + packet[43])
            # TODO: Account for transmission delay and fractional seconds.
            set_millis((ntp_time - NTP_OFFSET) * 1000)
    finally:
        s.close()


def get_tm():
    # Returns the current time as a struct tm in UTC.
    return millis_to_tm(get_millis())


def millis_to_tm(millis):
    # In CircuitPython, there are no time zones; time.localtime works in UTC.
    return time.localtime(max(millis, MIN_MILLIS)//1000)


def tm_to_millis(tm):
    # In CircuitPython, there are no time zones; time.mktime works in UTC.
    return int(time.mktime(tm)*1000)


def sleep_millis(ms):
    # Advances the time by the given amount.
    wake_millis = get_millis() + ms
    while get_millis() < wake_millis:
        pass


def try_isoformat_to_millis(data, key):
    # Parses a yyyy-mm-ddThh:mm:ss string into a time in millis.
    iso = data.get(key)
    try:
        assert iso[4] + iso[7] + iso[10] + iso[13] + iso[16] == '--T::'
        y, l, d = iso[:4], iso[5:7], iso[8:10]
        h, m, s = iso[11:13], iso[14:16], iso[17:19]
        tm = (int(y), int(l), int(d), int(h), int(m), int(s), 0, 0, 0)
        return tm_to_millis(tm)
    except Exception as e:
        print('Invalid timestamp for %r: %r' % (key, iso))


def millis_to_isoformat(millis):
    # Formats a time in millis into a yyyy-mm-ddThh:mm:ss string.
    return '%04d-%02d-%02dT%02d:%02d:%02d' % millis_to_tm(millis)[:6]
