import utils

utils.mem('app1')
import ccapi
utils.mem('app2')
import cctime
utils.mem('app3')
from ccinput import DialReader
utils.mem('app4')
from clock_mode import ClockMode
utils.mem('app5')
from menu_mode import MenuMode
utils.mem('app6')
from pref_entry_mode import PrefEntryMode
utils.mem('app7')
from prefs import Prefs
utils.mem('app8')
from utils import Cycle


class App:
    def __init__(self, fs, network, frame, button_map, dial_map):
        utils.mem('App.__init__')
        self.network = network
        self.frame = frame
        self.frame_counter = FrameCounter()
        self.prefs = Prefs(fs)

        self.clock_mode = ClockMode(self, fs, network, button_map)
        self.menu_mode = MenuMode(self, button_map, dial_map)
        self.wifi_ssid_mode = PrefEntryMode(
            self, 'Wi-Fi network name:', 'wifi_ssid', button_map, dial_map)
        self.wifi_password_mode = PrefEntryMode(
            self, 'Wi-Fi password:', 'wifi_password', button_map, dial_map)
        self.mode = self.clock_mode

        self.langs = Cycle('en', 'es', 'de', 'fr', 'is')
        self.lang = self.langs.current()
        self.brightness_reader = DialReader(
            'BRIGHTNESS', dial_map['BRIGHTNESS'], 3/32.0, 0.01, 0.99)
        utils.mem('App.__init__ done')

    def start(self):
        self.frame.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
        self.frame_counter.tick()
        utils.mem('step')
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
        self.mode.receive(command, arg)

    def set_mode(self, mode):
        self.frame.clear()
        self.mode.end()
        self.mode = mode
        mode.start()


class FrameCounter:
    def __init__(self):
        self.start = cctime.monotonic()
        self.frame_count = 0
        self.fps = 0
        self.last_tick = self.start
        self.next_report = self.start + 10

    def tick(self):
        print('.', end='')
        now = cctime.monotonic()
        duration = now - self.last_tick
        if duration > 0:
            last_fps = 1.0/duration
            self.fps = 0.9 * self.fps + 0.1 * last_fps
        self.frame_count += 1
        self.last_tick = now

        if now > self.next_report:
            print(f'uptime: {now - self.start:.1f} s / {self.fps:.1f} fps')
            self.next_report += 10


utils.mem('app12')


def run(fs, network, frame, button_map, dial_map):
    cctime.enable_rtc()
    app = App(fs, network, frame, button_map, dial_map)
    app.start()
    while True:
        app.step()
