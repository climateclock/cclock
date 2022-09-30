import cctime
import os
import time

rtc_offset = cctime.MIN_MILLIS//1000 - time.time()

# By default, pretend the internal clock is 2% too slow.
internal_clock_speed = int(os.environ.get('CCLOCK_CLOCK_SPEED_PERCENT', 98))/100

def fake_monotonic_millis():
    return int(internal_clock_speed * time.monotonic_ns()/1000000)

def fake_rtc_getter():
    return time.localtime(int(time.time() + rtc_offset))

def fake_rtc_setter(tm):
    global rtc_offset
    rtc_offset = time.mktime(tm) - time.time()

def fake_enable_rtc():
    # Simulate an RTC with accurate ticks but a possible offset.
    global rtc_offset
    cctime.rtc_getter = fake_rtc_getter
    cctime.rtc_setter = fake_rtc_setter

def install():
    cctime.monotonic_millis = fake_monotonic_millis
    cctime.enable_rtc = fake_enable_rtc
