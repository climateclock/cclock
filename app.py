import ccapi
import cctime
from ccinput import DialReader
from clock_mode import ClockMode
import gc
from menu_mode import MenuMode
from pref_entry_mode import PrefEntryMode
from prefs import Prefs
from utils import Cycle, mem


class App:
    def __init__(self, prefs, network, frame, fs, button_map, dial_map):
        mem('pre-App.__init__')
        self.prefs = prefs
        self.network = network
        self.frame = frame
        self.frame_counter = FrameCounter()

        self.clock_mode = ClockMode(self, fs, network, button_map, dial_map)
        mem('ClockMode')
        self.menu_mode = MenuMode(self, button_map, dial_map)
        mem('MenuMode')
        self.wifi_ssid_mode = PrefEntryMode(
            self, 'Wi-Fi network name', 'wifi_ssid', button_map, dial_map)
        mem('PrefEntryMode')
        self.wifi_password_mode = PrefEntryMode(
            self, 'Wi-Fi password', 'wifi_password', button_map, dial_map)
        mem('PrefEntryMode')
        self.custom_message_mode = PrefEntryMode(
            self, 'Custom message', 'custom_message', button_map, dial_map)
        mem('PrefEntryMode')
        self.mode = self.clock_mode

        self.langs = Cycle('en', 'es', 'de', 'fr', 'is')
        self.lang = self.langs.current()
        self.brightness_reader = DialReader(
            'BRIGHTNESS', dial_map['BRIGHTNESS'], 3/32.0, 0.01, 0.99)
        mem('App.__init__')

    def start(self):
        self.frame.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
        gc.collect()
        if hasattr(gc, 'mem_free'):
            print(gc.mem_free())
        self.frame_counter.tick()
        self.brightness_reader.step(self.receive)
        self.mode.step()

    def receive(self, command, arg=None):
        print('[' + command + ('' if arg is None else ': ' + str(arg)) + ']')
        if command == 'BRIGHTNESS':
            delta, value = arg
            self.frame.set_brightness(value)
        if command == 'NEXT_LANGUAGE':
            self.lang = self.langs.next()
            self.frame.clear()
        if command == 'CLOCK_MODE':
            self.set_mode(self.clock_mode)
        if command == 'MENU_MODE':
            self.set_mode(self.menu_mode)
        if command == 'WIFI_SSID_MODE':
            self.set_mode(self.wifi_ssid_mode)
        if command == 'WIFI_PASSWORD_MODE':
            self.set_mode(self.wifi_password_mode)
        if command == 'CUSTOM_MESSAGE_MODE':
            self.set_mode(self.custom_message_mode)
        self.mode.receive(command, arg)

    def set_mode(self, mode):
        self.frame.clear()
        self.mode.end()
        self.mode = mode
        mode.start()


class FrameCounter:
    def __init__(self):
        self.start = cctime.get_millis()
        self.frame_count = 0
        self.fps = 0
        self.last_tick = self.start
        self.next_report = self.start + 10000

    def tick(self):
        print('.', end='')
        now = cctime.get_millis()
        elapsed = now - self.last_tick
        if elapsed > 0:
            last_fps = 1000.0/elapsed
            self.fps = 0.9 * self.fps + 0.1 * last_fps
        self.frame_count += 1
        self.last_tick = now

        if now > self.next_report:
            print(f'uptime: {now - self.start:.1f} s / {self.fps:.1f} fps')
            self.next_report += 10000


def run(prefs, network, frame, fs, button_map, dial_map):
    cctime.enable_rtc()
    app = App(prefs, network, frame, fs, button_map, dial_map)
    app.start()
    while True:
        app.step()
