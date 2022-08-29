import ccapi
import cctime
from ccinput import DialReader
from clock_mode import ClockMode
import gc
from menu_mode import MenuMode
from pref_entry_mode import PrefEntryMode
from utils import Cycle, mem


class App:
    def __init__(self, network, frame, button_map, dial_map):
        mem('pre-App.__init__')
        self.network = network
        self.frame = frame
        self.frame_counter = FrameCounter()

        self.clock_mode = ClockMode(self, network, button_map, dial_map)
        mem('ClockMode')
        self.menu_mode = MenuMode(self, button_map, dial_map)
        mem('MenuMode')
        self.pref_entry_mode = PrefEntryMode(self, button_map, dial_map)
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
        mem('step')
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
            self.pref_entry_mode.set_pref('Wi-Fi network name', 'wifi_ssid')
            self.set_mode(self.pref_entry_mode)
        if command == 'WIFI_PASSWORD_MODE':
            self.pref_entry_mode.set_pref('Wi-Fi password', 'wifi_password')
            self.set_mode(self.pref_entry_mode)
        if command == 'CUSTOM_MESSAGE_MODE':
            self.pref_entry_mode.set_pref('Custom message', 'custom_message')
            self.set_mode(self.pref_entry_mode)
        if command == 'DUMP_MEMORY':
            import micropython
            gc.collect()
            micropython.mem_info(1)
        if command == 'DUMP_FRAME':
            print('[[FRAME]]')
            for y in range(32):
                for x in range(192):
                    cv = self.frame.bitmap[x, y]
                    print('%02x%02x%02x' % self.frame.unpack(cv), end='')
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
            print(f'uptime: {(now - self.start)/1000:.1f} s / {self.fps:.1f} fps')
            self.next_report += 10000


def run(network, frame, button_map, dial_map):
    cctime.enable_rtc()
    app = App(network, frame, button_map, dial_map)
    app.start()
    while True:
        app.step()
