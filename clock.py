import ccapi
import cctime
import ccui
from ccinput import ButtonReader, Press
import gc


menu = [
    'Brightness',
    'Wi-Fi connection',
    'Lifelines'
]


class Clock:
    def __init__(self, data, frame, button_map):
        self.data = data
        self.frame = frame
        self.state = 'CLOCK'
        self.state_steps = {
            'CLOCK': self.clock_step,
            'MENU': self.menu_step,
            'PASSWORD': self.password_step,
        }
        self.clock_reader = ButtonReader({
            button_map['NEXT']: {
                Press.SHORT: 'NEXT_LIFELINE',
            },
            button_map['ENTER']: {
                Press.LONG: 'MENU',
            }
        })
        self.menu_reader = ButtonReader({
            button_map['NEXT']: {
                Press.SHORT: 'NEXT_OPTION',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER',
                Press.LONG: 'PASSWORD'
            }
        })
        self.password_reader = ButtonReader({
            button_map['NEXT']: {
                Press.SHORT: 'NEXT_CHAR',
                Press.REPEAT: 'NEXT_CHAR',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'CLOCK'
            }
        })

        self.carbon_module = self.data.module_dict['carbon_deadline_1']
        self.lifeline_modules = [
            m for m in self.data.modules if m.flavor == 'lifeline']
        self.lifeline_index = 0

        # self.cv = self.frame.pack(*self.data.config.display.deadline.primary)
        self.cv = self.frame.pack(0xff, 0xff, 0xc1)

    def step(self):
        self.state_steps[self.state]()

    def clock_start(self):
        self.state = 'CLOCK'
        self.clock_reader.reset()

    def clock_step(self):
        ccui.render_deadline_module(
            self.frame, 0, self.carbon_module, self.cv)
        ccui.render_lifeline_module(
            self.frame, 16, self.lifeline_modules[self.lifeline_index], self.cv)
        self.clock_reader.step(self.receive)
        self.frame.send()

    def menu_start(self):
        self.frame.clear()
        label = self.frame.new_label('Brightness', 'kairon-10', self.cv)
        self.frame.paste(1, 0, label)
        label = self.frame.new_label('Wi-Fi connection', 'kairon-10', self.cv)
        self.frame.paste(1, 11, label)
        label = self.frame.new_label('Lifelines', 'kairon-10', self.cv)
        self.frame.paste(1, 22, label)
        self.state = 'MENU'
        self.menu_reader.reset()

    def menu_step(self):
        self.menu_reader.step(self.receive)
        self.frame.send()

    def password_start(self):
        self.frame.clear()
        label = self.frame.new_label('Wi-Fi password:', 'kairon-10', self.cv)
        self.frame.paste(1, 0, label)
        self.state = 'PASSWORD'

        self.charset = (
            ' ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'abcdefghijklmnopqrstuvwxyz'
            '0123456789.,:;!?'
            '\'"@#$%^&*+-_=*/()[]<>{}~\\'
        )
        self.char_index = 0
        self.char = self.charset[0]
        self.text = ''
        self.password_update_text()

    def password_step(self):
        self.password_reader.step(self.receive)
        self.frame.send()

    def password_update_char(self):
        self.char = self.charset[self.char_index]
        char_label = self.frame.new_label(self.char, 'kairon-10', self.cv)
        x = 1 + self.text_label.w
        self.frame.paste(x, 16, char_label)
        self.frame.fill(x, 26, char_label.w - 1, 1, self.cv)
        self.frame.clear(x + char_label.w - 1, 16, 10, 12)

    def password_update_text(self):
        self.text_label = self.frame.new_label(self.text, 'kairon-10', self.cv)
        self.frame.paste(1, 16, self.text_label)
        self.frame.clear(1, 26, self.text_label.w, 1)
        self.password_update_char()

    def receive(self, command):
        print(f'[{command}]')
        gc.collect()
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

    def incr_lifeline(self, delta):
        self.lifeline_index = (
            self.lifeline_index + len(self.lifeline_modules) + delta
        ) % len(self.lifeline_modules)


def run(frame, button_map):
    cctime.enable_rtc()
    data = ccapi.load_file('cache/climateclock.json')
    gc.collect()
    clock = Clock(data, frame, button_map)
    while True:
        clock.step()
