import ccapi
import cctime
import ccui
from ccinput import ButtonReader, Press


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
            'MENU': self.menu_step
        }
        self.clock_reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.DOUBLE: 'MENU'
            },
            button_map['DOWN']: {
                Press.SHORT: 'PREV_LIFELINE',
                Press.REPEAT: 'REPEAT_LIFELINE'
            }
        })
        self.menu_reader = ButtonReader({
            button_map['UP']: {
                Press.DOUBLE: 'CLOCK'
            },
        })

        self.carbon_module = self.data.module_dict['carbon_deadline_1']
        self.lifeline_modules = [
            m for m in self.data.modules if m.flavor == 'lifeline']
        self.lifeline_index = 0

        self.cv = self.frame.pack(*self.data.config.display.deadline.primary)

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
        self.frame.fill(0, 0, self.frame.w, self.frame.h, self.cv)
        label = self.frame.new_label('menu', 'helvetica-15', self.cv)
        self.frame.paste(0, 0, label)
        self.state = 'MENU'
        self.menu_reader.reset()

    def menu_step(self):
        self.menu_reader.step(self.receive)
        self.frame.send()

    def receive(self, command):
        print(f'[{command}]')
        if command == 'NEXT_LIFELINE':
            self.incr_lifeline(1)
        if command == 'PREV_LIFELINE':
            self.incr_lifeline(-1)
        if command == 'CLOCK':
            self.clock_start()
        if command == 'MENU':
            self.menu_start()

    def incr_lifeline(self, delta):
        self.lifeline_index = (
            self.lifeline_index + len(self.lifeline_modules) + delta
        ) % len(self.lifeline_modules)


def run(frame, button_map):
    cctime.enable_rtc()
    data = ccapi.load_file('cache/climateclock.json')
    clock = Clock(data, frame, button_map)
    while True:
        clock.step()
