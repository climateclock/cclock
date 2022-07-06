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


menu = [
    'Brightness',
    'Wi-Fi connection',
    'Lifelines'
]


class Clock:
    def __init__(self, data, frame, button_map, dial_map):
        debug.mem('Clock.__init__')

        self.data = data
        self.frame = frame
        self.langs = ['en', 'es', 'de', 'fr', 'is']
        self.lang_index = 0
        self.state = 'CLOCK'
        self.state_steps = {
            'CLOCK': self.clock_step,
            'MENU': self.menu_step,
            'PASSWORD': self.password_step,
        }
        self.clock_reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_LANGUAGE',
                Press.LONG: 'TOGGLE_CASE',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.LONG: 'MENU',
            },
            button_map['ENTER']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.SHORT: 'MENU',
            }
        })
        self.menu_reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_OPTION',
            },
            button_map['DOWN']: {
                Press.SHORT: 'PASSWORD',
            },
            button_map['ENTER']: {
                Press.SHORT: 'PASSWORD',
            }
        })
        self.password_reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_CHAR',
                Press.REPEAT: 'NEXT_CHAR',
            },
            button_map['DOWN']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'CLOCK',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'CLOCK',
            }
        })
        self.brightness_reader = DialReader('BRIGHTNESS', dial_map['BRIGHTNESS'], 3/32.0)
        self.menu_selector_reader = DialReader('MENU_SELECTOR', dial_map['SELECTOR'], 1)
        self.password_selector_reader = DialReader('PASSWORD_SELECTOR', dial_map['SELECTOR'], 1)

        self.carbon_module = self.data.module_dict['carbon_deadline_1']
        self.lifeline_modules = [
            m for m in self.data.modules if m.flavor == 'lifeline']
        self.lifeline_index = 0

        self.deadline_cv = self.frame.pack(*self.data.config.display.deadline.primary)
        self.lifeline_cv = self.frame.pack(*self.data.config.display.lifeline.primary)
        self.menu_cv = self.frame.pack(0x80, 0x80, 0x80)
        self.edit_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.force_upper = False

        self.start_time = cctime.get_time()
        self.auto_advance_interval = 30
        self.next_advance_time = self.start_time + self.auto_advance_interval
        self.frame_count = 0

        debug.mem('Clock.__init__ done')

    def step(self):
        debug.mem('step')
        self.brightness_reader.step(self.receive)
        self.state_steps[self.state]()
        self.frame_count += 1

        now = cctime.get_time()
        if now > self.next_advance_time:
            elapsed = now - self.start_time
            print(f'frames: {self.frame_count} / elapsed: {elapsed:.1f} / fps: {self.frame_count/elapsed:.1f}')
            self.incr_lifeline(1)
            self.next_advance_time += self.auto_advance_interval

    def clock_start(self):
        self.frame.clear()
        self.state = 'CLOCK'
        self.clock_reader.reset()

    def clock_step(self):
        lang = self.langs[self.lang_index]
        ccui.render_deadline_module(
            self.frame, 0, self.carbon_module,
            self.deadline_cv, lang, self.force_upper)
        self.clock_reader.step(self.receive)
        ccui.render_lifeline_module(
            self.frame, 16, self.lifeline_modules[self.lifeline_index],
            self.lifeline_cv, lang, self.force_upper)
        self.clock_reader.step(self.receive)
        self.frame.send()

    def menu_start(self):
        self.frame.clear()
        label = self.frame.new_label('Brightness', 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.menu_cv)
        label = self.frame.new_label('Wi-Fi connection', 'kairon-10')
        self.frame.paste(1, 11, label, cv=self.menu_cv)
        label = self.frame.new_label('Lifelines', 'kairon-10')
        self.frame.paste(1, 22, label, cv=self.menu_cv)
        self.state = 'MENU'
        self.menu_reader.reset()

    def menu_step(self):
        self.menu_selector_reader.step(self.receive)
        self.menu_reader.step(self.receive)
        self.frame.send()

    def password_start(self):
        self.frame.clear()
        label = self.frame.new_label('Wi-Fi password:', 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.menu_cv)
        self.state = 'PASSWORD'

        self.charset = (
            ' aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ' +
            '0123456789' +
            '.,:;!?' +
            '\'"@#$%^&*+-_=*' +
            '/\\()[]<>{}~'
        )
        self.char_index = 0
        self.char = self.charset[0]
        self.text = ''
        self.password_update_text()

    def password_step(self):
        self.password_selector_reader.step(self.receive)
        self.password_reader.step(self.receive)
        self.frame.send()

    def password_update_char(self):
        self.char = self.charset[self.char_index]
        char_label = self.frame.new_label(self.char, 'kairon-10')
        x = 1 + self.text_label.w
        self.frame.paste(x, 16, char_label, cv=self.edit_cv)
        self.frame.fill(x, 26, char_label.w - 1, 1, self.menu_cv)
        self.frame.clear(x + char_label.w - 1, 16, 10, 12)

    def password_update_text(self):
        self.text_label = self.frame.new_label(self.text, 'kairon-10')
        self.frame.paste(1, 16, self.text_label, cv=self.menu_cv)
        self.frame.clear(1, 26, self.text_label.w, 1)
        self.password_update_char()

    def receive(self, command, arg=None):
        if arg is not None:
            print(f'[{command}: {arg}]')
        else:
            print(f'[{command}]')
        if command == 'NEXT_LANGUAGE':
            self.frame.clear()
            self.lang_index = (self.lang_index + 1) % len(self.langs)
        if command == 'TOGGLE_CASE':
            self.frame.clear()
            self.force_upper = not self.force_upper
        if command == 'NEXT_LIFELINE':
            self.incr_lifeline(1)
        if command == 'PREV_LIFELINE':
            self.incr_lifeline(-1)
        if command == 'CLOCK':
            self.clock_start()
        if command == 'MENU':
            self.menu_start()
        if command == 'PASSWORD':
            self.password_start()
        if command == 'NEXT_CHAR':
            self.char_index = (self.char_index + 1) % len(self.charset)
            self.password_update_char()
        if command == 'ENTER_CHAR':
            self.text += self.char
            self.password_update_text()
        if command == 'BRIGHTNESS':
            delta, value = arg
            self.frame.set_brightness(value)
        if command == 'PASSWORD_SELECTOR':
            delta, value = arg
            self.char_index = (self.char_index + len(self.charset) + delta) % len(self.charset)
            self.password_update_char()

    def incr_lifeline(self, delta):
        self.frame.clear()
        self.lifeline_index = (
            self.lifeline_index + len(self.lifeline_modules) + delta
        ) % len(self.lifeline_modules)
        self.frame.clear()


debug.mem('clock6')


def run(frame, button_map, dial_map):
    cctime.enable_rtc()
    data = ccapi.load_file('cache/climateclock.json')
    clock = Clock(data, frame, button_map, dial_map)
    while True:
        clock.step()
