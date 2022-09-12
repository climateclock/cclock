import ccapi
import cctime
from ccinput import DialReader
from clock_mode import ClockMode
import gc
from menu_mode import MenuMode
import micropython
from pref_entry_mode import PrefEntryMode
from utils import Cycle, free, log


class App:
    def __init__(self, network, frame, button_map, dial_map):
        log('Starting App.__init__')
        self.network = network
        self.frame = frame
        self.frame_counter = FrameCounter()

        self.clock_mode = ClockMode(self, network, button_map, dial_map)
        log('Created ClockMode')
        self.menu_mode = MenuMode(self, button_map, dial_map)
        log('Created MenuMode')
        self.pref_entry_mode = PrefEntryMode(self, button_map, dial_map)
        log('Created PrefEntryMode')
        self.mode = self.clock_mode

        self.langs = Cycle('en', 'es', 'de', 'fr', 'is')
        self.lang = self.langs.get()
        self.brightness_reader = DialReader(
            'BRIGHTNESS', dial_map['BRIGHTNESS'], 3/32.0, 0.01, 0.99)
        log('Finished App.__init__')

    def start(self):
        self.frame.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
        self.frame_counter.tick()
        self.brightness_reader.step(self.receive)
        self.mode.step()

    def receive(self, command, arg=None):
        print('[' + command + ('' if arg is None else ': ' + str(arg)) + ']')
        if command == 'BRIGHTNESS':
            delta, value = arg
            self.frame.set_brightness(value)
        if command == 'NEXT_LANGUAGE':
            self.lang = self.langs.get(1)
            self.frame.clear()
        if command == 'CLOCK_MODE':
            self.set_mode(self.clock_mode)
        if command == 'MENU_MODE':
            self.set_mode(self.menu_mode)
        if command == 'WIFI_SSID_MODE':
            self.pref_entry_mode.set_pref('Wi-Fi network name', 'wifi_ssid')
            self.set_mode(self.pref_entry_mode)
        if command == 'WIFI_PASSWORD_MODE':
            self.pref_entry_mode.set_pref('Wi-Fi password', 'wifi_password')
            self.set_mode(self.pref_entry_mode)
        if command == 'CUSTOM_MESSAGE_MODE':
            self.pref_entry_mode.set_pref('Custom message', 'custom_message')
            self.set_mode(self.pref_entry_mode)
        if command == 'DUMP_MEMORY':
            gc.collect()
            micropython.mem_info(1)
        if command == 'DUMP_FRAME':
            print('[[FRAME]]')
            cvs = ['%02x%02x%02x' % self.frame.unpack(cv) for cv in range(16)]
            for i in range(192*32):
                print(cvs[self.frame.bitmap[i]], end='')
            print()
            gc.collect()

        self.mode.receive(command, arg)

    def set_mode(self, mode):
        self.frame.clear()
        self.mode.end()
        self.mode = mode
        mode.start()


class FrameCounter:
    def __init__(self):
        self.start = cctime.monotonic_millis()
        self.fps = 0
        self.last_tick = self.start
        self.min_free = free()

    def tick(self):
        now = cctime.monotonic_millis()
        elapsed = now - self.last_tick
        if elapsed > 0:
            last_fps = 1000.0/elapsed
            self.fps = 0.9 * self.fps + 0.1 * last_fps
        last_sec = self.last_tick//1000
        now_sec = now//1000
        if now_sec > last_sec:
            print('|\n', end='')
            if now_sec % 10 == 0:
                log(f'Uptime {self.uptime()} s ({self.fps:.1f} fps, {self.mem()} free)')
        print('.', end='')
        self.last_tick = now

    def uptime(self):
        now = cctime.monotonic_millis()
        return (now - self.start)//1000

    def mem(self):
        now_free = free()
        self.min_free = min(self.min_free, now_free)
        return now_free


def run(network, frame, button_map, dial_map):
    log('Starting run')
    cctime.enable_rtc()
    app = App(network, frame, button_map, dial_map)
    app.start()
    log('First frame')
    while True:
        app.step()
