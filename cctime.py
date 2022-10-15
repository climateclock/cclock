"""Time-handling functions that work in both Python and CircuitPython."""

import time
import utils

# Offset of Unix epoch (1970-01-01) from NTP epoch (1900-01-01), in seconds
NTP_OFFSET = 2208988800

# CircuitPython cannot perform time calculations before 2000
MIN_MILLIS = 946684800_000  # 2000-01-01 00:00:00 UTC represented as Unix time

# Unix time in ms that corresponds to monotonic_ns() == 0
ref_millis = MIN_MILLIS  # the board starts up with the clock set to 2000-01-01
rtc_getter = None
rtc_setter = None


def monotonic_millis():
    return time.monotonic_ns()//1000000


def get_millis():
    return ref_millis + monotonic_millis()


def set_millis(millis):
    global ref_millis
    print(f'Setting cctime clock to {millis} ({millis_to_isoformat(millis)})')
    ref_millis = millis - monotonic_millis()
    if rtc_setter:
        # To set the RTC with sub-second precision, we wait until the
        # transition to the next second to set it.  Allow an extra 10 ms to
        # account for time passing while we're doing this work.
        set_millis = ((millis + 10)//1000 + 1) * 1000
        tm = time.localtime(set_millis//1000)
        print('Setting RTC to', tm)
        sleep_millis(set_millis - millis)
        rtc_setter(tm)


def enable_rtc():
    # Activates use of an attached DS3231 RTC as the time source.
    global rtc_getter, rtc_setter
    try:
        import board
        from adafruit_bus_device.i2c_device import I2CDevice
        from adafruit_register.i2c_bcd_datetime import BCDDateTimeRegister
    except:
        print(f'RTC access libraries are unavailable')
        return
    try:
        register = BCDDateTimeRegister(0)
        class DS3231:
            i2c_device = I2CDevice(board.I2C(), 0x68)
        rtc_getter = lambda: register.__get__(DS3231)
        rtc_setter = lambda tm: register.__set__(DS3231, tm)
    except Exception as e:
        rtc_getter = None
        rtc_setter = None
        utils.report_error(e, 'Could not find an attached DS3231 RTC')


def rtc_sync():
    # Updates the clock offset so that get_millis() is in sync with the RTC.
    # time.monotonic_ns() is driven by an internal clock that can be off by
    # as much as 1%, so we must call rtc_sync() often to avoid drift.
    global ref_millis
    if rtc_getter:
        now_millis = get_millis()
        now_sec = now_millis//1000
        rtc_sec = int(time.mktime(rtc_getter()))
        if now_sec < rtc_sec:
            ref_millis += rtc_sec * 1000 - now_millis
            print('>', end='')
        elif now_sec > rtc_sec:
            ref_millis -= now_millis - (rtc_sec + 1) * 1000
            print('<', end='')


def ntp_sync(socklib, server):
    # Gets the time from an NTP server and sets the clock accordingly.
    sock = socklib.socket(type=socklib.SOCK_DGRAM)
    sock.settimeout(1)
    try:
        addr = socklib.getaddrinfo(server, 123)[0][4]
        sock.connect(addr, conntype=1)  # esp.UDP_MODE == 1
        packet = bytearray(48)
        packet[0] = 0b_00_100_011  # no leap second, NTP version 4, client mode
        send_millis = monotonic_millis()
        sock.send(packet)
        if sock.recv_into(packet) == 48:
            recv_millis = monotonic_millis()
            ntp_time = ((packet[40] << 24) + (packet[41] << 16) +
                (packet[42] << 8) + packet[43]) - NTP_OFFSET
            ntp_millis = ntp_time * 1000 + (packet[44] * 1000 // 256)
            latency_millis = (recv_millis - send_millis)//2
            print(f'Got {server} time {ntp_millis}, latency {latency_millis}')

            new_millis = ntp_millis - latency_millis
            current_millis = get_millis()
            if abs(new_millis - current_millis) < 1000:
                # For small adjustments, average a few measurements over time.
                delta_millis = (new_millis - current_millis) // 5
                print(f'Adjusting clock toward {new_millis} by {delta_millis}')
                new_millis = current_millis + delta_millis
            set_millis(new_millis)
    except Exception as e:
        utils.report_error(e, 'Failed to get NTP time')
    finally:
        sock.close()


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
    if iso is None:
        return None
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
    if millis != None:
        return '%04d-%02d-%02dT%02d:%02d:%02d' % millis_to_tm(millis)[:6]
