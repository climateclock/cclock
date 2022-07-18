from ccinput import ButtonReader, Press
import cctime
import ccui
from mode import Mode
from utils import Cycle


class ClockMode(Mode):
    def __init__(self, app, fs, network, defn, button_map):
        super().__init__(app)
        self.fs = fs
        self.network = network
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

        if cctime.monotonic() > self.next_advance:
            self.next_advance += self.auto_advance_interval
            self.lifeline_module = self.lifeline_modules.next()
            self.frame.clear()

    def receive(self, command, arg=None):
        if command == 'TOGGLE_CAPS':
            self.force_caps = not self.force_caps
            self.frame.clear()
        if command == 'NEXT_LIFELINE':
            self.lifeline_module = self.lifeline_modules.next()
            self.frame.clear()
