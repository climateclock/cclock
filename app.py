import ccapi
import cctime
from ccinput import DialReader
from clock_mode import ClockMode
import display
import fs
import gc
from menu_mode import MenuMode
import microcontroller
import network
from edit_mode import EditMode
import storage
import utils


class App:
    def __init__(self, bitmap, net, power_sensor, button_map, dial_map):
        utils.log('Starting App.__init__')
        self.bitmap = bitmap
        self.net = net
        self.power_sensor = power_sensor
        self.frame_counter = FrameCounter()

        self.clock_mode = ClockMode(self, net, button_map, dial_map)
        utils.log('Created ClockMode')
        self.menu_mode = MenuMode(self, button_map, dial_map)
        utils.log('Created MenuMode')
        self.edit_mode = EditMode(self, button_map, dial_map)
        utils.log('Created EditMode')
        self.mode = self.clock_mode

        self.langs = utils.Cycle(['en', 'es', 'de', 'fr', 'is'])
        self.lang = self.langs.get()
        self.brightness_reader = DialReader(
            'BRIGHTNESS', dial_map['BRIGHTNESS'], 9/256, 1/256, 255/256)
        utils.log('Finished App.__init__')

    def start(self):
        display.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
        if self.power_sensor.level < 5:
            self.shut_down()
        self.frame_counter.tick()
        cctime.rtc_sync()
        self.brightness_reader.step(self)
        self.mode.step()

    def shut_down(self):
        utils.log(f'Power level is {self.power_sensor.level}%; shutting down')
        storage.umount('/')
        utils.log(f'Storage has been unmounted')
        display.blank()
        while self.power_sensor.level < 5:
            display.send()
        utils.log(f'Power has returned after shutdown; restarting')
        microcontroller.reset()

    def receive(self, command, arg=None):
        print('[' + command + ('' if arg is None else ': ' + str(arg)) + ']')
        if command == 'BRIGHTNESS':
            delta, value = arg
            display.set_brightness(value)
        if command == 'NEXT_LANGUAGE':
            self.lang = self.langs.get(1)
            self.bitmap.fill(0)
        if command == 'CLOCK_MODE':
            self.set_mode(self.clock_mode)
        if command == 'MENU_MODE':
            self.set_mode(self.menu_mode)
        if command == 'WIFI_SSID_MODE':
            self.edit_mode.set_pref('Wi-Fi network name', 'wifi_ssid')
            self.set_mode(self.edit_mode)
        if command == 'WIFI_PASSWORD_MODE':
            self.edit_mode.set_pref('Wi-Fi password', 'wifi_password')
            self.set_mode(self.edit_mode)
        if command == 'CUSTOM_MESSAGE_MODE':
            self.edit_mode.set_pref(
                'Custom message', 'custom_message', True)
            self.set_mode(self.edit_mode)
        if command == 'DUMP_MEMORY':
            utils.log('Memory layout', True)
        if command == 'DUMP_FRAME':
            utils.log('Frame dump')
            rgbs = ['%02x%02x%02x' % display.get_rgb(pi) for pi in range(16)]
            for i in range(192*32):
                print(rgbs[self.bitmap[i]], end='')
            print('\n[[FRAME]]')
            gc.collect()

        self.mode.receive(command, arg)

    def set_mode(self, mode):
        self.bitmap.fill(0)
        self.mode = mode
        mode.start()


class FrameCounter:
    def __init__(self):
        self.start = cctime.monotonic_millis()
        self.fps = 0
        self.last_tick = self.start

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
                utils.log(f'Up {self.uptime()} s ({self.fps:.1f} fps) on {utils.version_dir()}')
        print('.', end='')
        self.last_tick = now

    def uptime(self):
        now = cctime.monotonic_millis()
        return (now - self.start)//1000


class Indicator:
    def __init__(self, bitmap, pi):
        self.depth = 0
        self.bitmap = bitmap
        self.pi = pi

    def __enter__(self):
        self.depth += 1
        self.bitmap.fill(self.pi, 191, 0, 192, 1)
        display.send()

    def __exit__(self, *args):
        self.depth -= 1
        if self.depth == 0:
            self.bitmap.fill(0, 191, 0, 192, 1)


def run(bitmap, net, power_sensor, button_map, dial_map):
    fs.write_indicator = Indicator(bitmap, display.get_pi(0xff, 0x80, 0x00))
    net.indicator = Indicator(bitmap, display.get_pi(0x00, 0xff, 0x00))
    utils.log('Starting run')
    cctime.enable_rtc()
    app = App(bitmap, net, power_sensor, button_map, dial_map)
    app.start()
    utils.log('First frame')
    while True:
        app.step()
