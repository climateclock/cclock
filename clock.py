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
import pack_fetcher
debug.mem('clock6')
from network import State
debug.mem('clock7')


menu = [
    'Brightness',
    'Wi-Fi connection',
    'Lifelines'
]


class Cycle:
    def __init__(self, *items):
        self.items = items
        self.index = 0

    def current(self):
        return self.items[self.index]

    def next(self):
        self.index = (self.index + 1) % len(self.items)
        return self.items[self.index]


class App:
    def __init__(self, fs, network, defn, frame, button_map, dial_map):
        debug.mem('Clock.__init__')
        self.network = network
        self.frame = frame

        self.clock_mode = ClockMode(self, fs, network, defn, button_map)
        self.menu_mode = MenuMode(self, button_map, dial_map)
        self.password_mode = PasswordMode(self, button_map, dial_map)
        self.mode = self.clock_mode

        self.langs = Cycle('en', 'es', 'de', 'fr', 'is')
        self.lang = self.langs.current()

        self.brightness_reader = DialReader('BRIGHTNESS', dial_map['BRIGHTNESS'], 3/32.0)
        debug.mem('Clock.__init__ done')

    def start(self):
        self.frame.set_brightness(self.brightness_reader.value)
        self.mode.start()

    def step(self):
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
        if command == 'PASSWORD_MODE':
            self.set_mode(self.password_mode)
        self.mode.receive(command, arg)

    def set_mode(self, mode):
        self.mode.end()
        self.mode = mode
        mode.start()


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
        self.start_time = cctime.get_time()
        self.pack_fetch_interval = 30 * 60  # wait 30 minutes between fetches
        self.next_fetch_time = self.start_time + 5
        self.auto_advance_interval = 30
        self.next_advance_time = self.start_time + self.auto_advance_interval
        self.frame_count = 0

        self.reader.reset()
        self.frame.clear()

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

        self.frame_count += 1
        now = cctime.get_time()
        if now > self.next_advance_time:
            self.next_advance_time += self.auto_advance_interval
            elapsed = now - self.start_time
            print(f'frames: {self.frame_count} / elapsed: {elapsed:.1f} / fps: {self.frame_count/elapsed:.1f}')
            self.lifeline_module = self.lifeline_modules.next()
            self.frame.clear()

    def ota_step(self):
        if self.network.state == State.OFFLINE:
            self.network.enable_step('climateclock', 'climateclock')
            self.fetcher = None
        elif self.network.state == State.ONLINE:
            self.network.connect_step('zestyping.github.io')
            self.fetcher = None
        if self.network.state == State.CONNECTED:
            if not self.fetcher and cctime.get_time() > self.next_fetch_time:
                # TODO: instantiate PackFetcher just once
                self.fetcher = pack_fetcher.PackFetcher(
                    self.fs, self.network, b'zestyping.github.io', b'/test.pk')
                self.next_fetch_time += self.pack_fetch_interval
            if self.fetcher:
                try:
                    self.fetcher.next_step()
                except StopIteration:
                    print('Fetch completed successfully')
                    self.fetcher = None
                except Exception as e:
                    print(f'Fetcht aborted due to {e} ({repr(e)})')
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
        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_OPTION',
            },
            button_map['DOWN']: {
                Press.SHORT: 'PASSWORD_MODE',
            },
            button_map['ENTER']: {
                Press.SHORT: 'PASSWORD_MODE',
            }
        })
        self.dial_reader = DialReader('MENU_SELECTOR', dial_map['SELECTOR'], 1)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)

    def start(self):
        self.reader.reset()
        self.frame.clear()

        label = self.frame.new_label('Brightness', 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.cv)
        label = self.frame.new_label('Wi-Fi connection', 'kairon-10')
        self.frame.paste(1, 11, label, cv=self.cv)
        label = self.frame.new_label('Lifelines', 'kairon-10')
        self.frame.paste(1, 22, label, cv=self.cv)
        self.reader.reset()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()


class PasswordMode(Mode):
    def __init__(self, app, button_map, dial_map):
        super().__init__(app)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_CHAR',
                Press.REPEAT: 'NEXT_CHAR',
            },
            button_map['DOWN']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'CLOCK_MODE',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'CLOCK_MODE',
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
        self.frame.clear()

        label = self.frame.new_label('Wi-Fi password:', 'kairon-10')
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


debug.mem('clock8')


def run(fs, network, frame, button_map, dial_map):
    cctime.enable_rtc()
    data = ccapi.load_file('cache/climateclock.json')
    app = App(fs, network, data, frame, button_map, dial_map)
    app.start()
    while True:
        app.step()
