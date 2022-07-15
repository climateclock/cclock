import debug

debug.mem('clock1')
import ccapi
debug.mem('clock2')
import cctime
debug.mem('clock3')
import ccui
debug.mem('clock4')
from ccinput import ButtonReader, DialReader, Press
debug.mem('clock5')
import json
import os
debug.mem('clock6')
from network import State
debug.mem('clock7')
import pack_fetcher
debug.mem('clock8')


class App:
    def __init__(self, fs, network, defn, frame, button_map, dial_map):
        debug.mem('Clock.__init__')
        self.network = network
        self.frame = frame
        self.frame_counter = FrameCounter()
        self.prefs = Prefs(fs)
        self.prefs.set(
            'wifi_ssid', self.prefs.get('wifi_ssid', 'climateclock'))
        self.prefs.set(
            'wifi_password', self.prefs.get('wifi_password', 'climateclock'))

        self.clock_mode = ClockMode(self, fs, network, defn, button_map)
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
        debug.mem('Clock.__init__ done')

    def start(self):
        self.frame.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
        self.frame_counter.tick()
        debug.mem('step')
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


class Cycle:
    def __init__(self, *items):
        self.items = items
        self.index = 0

    def current(self):
        return self.items[self.index]

    def next(self):
        self.index = (self.index + 1) % len(self.items)
        return self.items[self.index]


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


class Prefs:
    def __init__(self, fs):
        self.fs = fs
        try:
            self.prefs = json.load(self.fs.open(b'/prefs.json'))
        except Exception as e:
            print(f'Could not read prefs.json: {e}')
            self.prefs = {}
        self.get = self.prefs.get

    def set(self, name, value):
        if self.prefs.get(name) != value:
            self.prefs[name] = value
            try:
                with self.fs.open(b'/prefs.json.new', 'wb') as file:
                    json.dump(self.prefs, file)
                self.fs.rename(b'/prefs.json.new', b'/prefs.json')
            except OSError as e:
                print(f'Could not write prefs.json: {e}')


class Mode:
    def __init__(self, app):
        self.app = app
        self.frame = app.frame

    def start(self):
        self.frame.clear()

    def step(self):
        pass

    def receive(self, command, arg=None):
        pass

    def end(self):
        pass


class ClockMode(Mode):
    def __init__(self, app, fs, network, defn, button_map):
        super().__init__(app)
        self.fs = fs
        self.network = network
        self.fetcher = None
        self.set_defn(defn)

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_LANGUAGE',
                Press.LONG: 'TOGGLE_CAPS',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.LONG: 'MENU_MODE',
            },
            button_map['ENTER']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.SHORT: 'MENU_MODE',
            }
        })
        self.force_caps = False

    def set_defn(self, defn):
        self.carbon_module = defn.module_dict['carbon_deadline_1']
        self.lifeline_modules = Cycle(*[m for m in defn.modules if m.flavor == 'lifeline'])
        self.lifeline_module = self.lifeline_modules.current()
        self.deadline_cv = self.frame.pack(*defn.config.display.deadline.primary)
        self.lifeline_cv = self.frame.pack(*defn.config.display.lifeline.primary)

    def start(self):
        self.reader.reset()
        self.frame.clear()
        now = cctime.monotonic()
        self.pack_fetch_interval = 30 * 60  # wait 30 minutes between fetches
        self.next_fetch = now + 3
        self.auto_advance_interval = 60
        self.next_advance = now + self.auto_advance_interval

    def step(self):
        ccui.render_deadline_module(
            self.frame, 0, self.carbon_module,
            self.deadline_cv, self.app.lang, self.force_caps)
        ccui.render_lifeline_module(
            self.frame, 16, self.lifeline_module,
            self.lifeline_cv, self.app.lang, self.force_caps)
        self.reader.step(self.app.receive)
        self.frame.send()

        self.ota_step()

        if cctime.monotonic() > self.next_advance:
            self.next_advance += self.auto_advance_interval
            self.lifeline_module = self.lifeline_modules.next()
            self.frame.clear()

    def ota_step(self):
        if self.network.state == State.OFFLINE:
            self.network.enable_step(
                self.app.prefs.get('wifi_ssid'),
                self.app.prefs.get('wifi_password')
            )
            self.fetcher = None
        elif self.network.state == State.ONLINE:
            self.network.connect_step('zestyping.github.io')
            self.fetcher = None
        if self.network.state == State.CONNECTED:
            if not self.fetcher and cctime.monotonic() > self.next_fetch:
                # TODO: instantiate PackFetcher just once
                self.fetcher = pack_fetcher.PackFetcher(
                    self.fs, self.network, b'zestyping.github.io', b'/test.pk')
                self.next_fetch += self.pack_fetch_interval
            if self.fetcher:
                try:
                    self.fetcher.next_step()
                except StopIteration:
                    print('Fetch completed successfully!')
                    self.fetcher = None
                except Exception as e:
                    print(f'Fetch aborted due to {e} ({repr(e)})')
                    self.fetcher = None

    def receive(self, command, arg=None):
        if command == 'TOGGLE_CAPS':
            self.force_caps = not self.force_caps
            self.frame.clear()
        if command == 'NEXT_LIFELINE':
            self.lifeline_module = self.lifeline_modules.next()
            self.frame.clear()


class MenuMode(Mode):
    def __init__(self, app, button_map, dial_map):
        super().__init__(app)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.cursor_label = self.frame.new_label('>', 'kairon-10')

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'PREV_OPTION',
                Press.LONG: 'CANCEL',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_OPTION',
                Press.LONG: 'PROCEED',
            },
            button_map['ENTER']: {
                Press.SHORT: 'PROCEED',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        wifi_ssid = self.app.prefs.get('wifi_ssid')
        firmware_version = self.app.network.get_firmware_version()
        hardware_address = self.app.network.get_hardware_address()
        self.tree = ('Settings', None, [
            ('Wi-Fi setup', None, [
                ('Network: ' + wifi_ssid, ('WIFI_SSID_MODE', None), []),
                ('Password', ('WIFI_PASSWORD_MODE', None), []),
                ('Back', ('CANCEL', None), [])
            ]),
            ('Auto cycling', None, [
                ('Off', ('SET_CYCLING', 0), []),
                ('15 seconds', ('SET_CYCLING', 15), []),
                ('60 seconds', ('SET_CYCLING', 60), []),
                ('Back', ('CANCEL', None), [])
            ]),
            ('System info', None,  [
                ('Action Clock v4', None, []),
                ('ESP firmware: ' + firmware_version, None, []),
                ('MAC ID: ' + hardware_address, None, []),
                ('Back', ('CANCEL', None), [])
            ]),
            ('Exit', ('CLOCK_MODE', None), [])
        ])
        self.crumbs = []
        self.top = 0
        self.index = 0
        self.proceed(self.tree)

    def proceed(self, node):
        label = self.frame.new_label('Hello', 'kairon-10')
        title, command_arg, children = node
        if command_arg:
            self.app.receive(*command_arg)
        else:
            self.crumbs.append((node, self.top, self.index))
            self.top = 0
            self.index = 0
            self.draw()

    def draw(self):
        (title, command, children), _, _ = self.crumbs[-1]
        self.frame.clear()
        label = self.frame.new_label(title, 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.cv)
        y = 0
        for index in range(self.top, self.top + 3):
            if index >= len(children):
                break
            child = children[index]
            label = self.frame.new_label(child[0], 'kairon-10')
            self.frame.paste(64, y, label, cv=self.cv)
            if index == self.index:
                self.frame.paste(58, y, self.cursor_label, cv=self.cursor_cv)
            y += 11

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def receive(self, command, arg=None):
        if command == 'SELECTOR':
            delta, value = arg
            self.move_cursor(delta)
        if command == 'PREV_OPTION':
            self.move_cursor(-1)
        if command == 'NEXT_OPTION':
            self.move_cursor(1)
        if command == 'PROCEED':
            (title, command_arg, children), _, _ = self.crumbs[-1]
            self.proceed(children[self.index])
        if command == 'CANCEL':
            _, self.top, self.index = self.crumbs.pop()
            self.draw()

    def move_cursor(self, delta):
        (title, command, children), _, _ = self.crumbs[-1]
        self.index = max(0, min(len(children) - 1, self.index + delta))
        self.top = max(self.index - 2, min(self.index, self.top))
        self.draw()


class PrefEntryMode(Mode):
    def __init__(self, app, pref_title, pref_name, button_map, dial_map):
        super().__init__(app)
        self.pref_title = pref_title
        self.pref_name = pref_name
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_CHAR',
                Press.REPEAT: 'NEXT_CHAR',
            },
            button_map['DOWN']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'SAVE_PREF',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'SAVE_PREF',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)
        self.charset = (
            ' aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ' +
            '0123456789' +
            '.,:;!?' +
            '\'"@#$%^&*+-_=*' +
            '/\\()[]<>{}~'
        )
        self.char_index = 0

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        label = self.frame.new_label(self.pref_title, 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.cv)
        self.text = ''
        self.draw_text()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def draw_char(self):
        self.char = self.charset[self.char_index]
        char_label = self.frame.new_label(self.char, 'kairon-10')
        x = 1 + self.text_label.w
        self.frame.paste(x, 16, char_label, cv=self.cursor_cv)
        self.frame.fill(x, 26, char_label.w - 1, 1, self.cv)
        self.frame.clear(x + char_label.w - 1, 16, 10, 12)

    def draw_text(self):
        self.text_label = self.frame.new_label(self.text, 'kairon-10')
        self.frame.paste(1, 16, self.text_label, cv=self.cv)
        self.frame.clear(1, 26, self.text_label.w, 1)
        self.draw_char()

    def receive(self, command, arg=None):
        if command == 'NEXT_CHAR':
            self.char_index = (self.char_index + 1) % len(self.charset)
            self.draw_char()
        if command == 'SELECTOR':
            delta, value = arg
            self.char_index = (self.char_index + len(self.charset) + delta) % len(self.charset)
            self.draw_char()
        if command == 'ENTER_CHAR':
            self.text += self.char
            self.draw_text()
        if command == 'SAVE_PREF':
            self.app.prefs.set(self.pref_name, self.text)
            self.app.receive('MENU_MODE')


debug.mem('clock9')


def run(fs, network, frame, button_map, dial_map):
    cctime.enable_rtc()
    data = ccapi.load_file('cache/climateclock.json')
    app = App(fs, network, data, frame, button_map, dial_map)
    app.start()
    while True:
        app.step()
