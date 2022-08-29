import ccapi
from ccinput import ButtonReader, DialReader, Press
import cctime
import ccui
import fs
from mode import Mode
import prefs
from updater import SoftwareUpdater
import utils
from utils import Cycle, mem


class ClockMode(Mode):
    def __init__(self, app, network, button_map, dial_map):
        mem('pre-ClockMode.__init__')
        super().__init__(app)
        self.network = network

        self.updater = SoftwareUpdater(network, self)
        mem('SoftwareUpdater')
        self.deadline = None
        self.lifeline = None
        self.message_module = ccapi.Newsfeed('newsfeed', '', [], [])
        mem('Newsfeed')

        self.reload_definition()
        mem('reload_definition')

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_LANGUAGE',
                Press.LONG: 'TOGGLE_CAPS',
                Press.DOUBLE: 'DUMP_FRAME',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.LONG: 'MENU_MODE',
                Press.DOUBLE: 'DUMP_MEMORY',
            },
            button_map['ENTER']: {
                Press.SHORT: 'NEXT_LIFELINE',
            }
        })
        mem('ButtonReader')
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)
        mem('DialReader')
        self.force_caps = False

    def reload_definition(self):
        try:
            with fs.open('/cache/clock.json') as api_file:
                defn = ccapi.load(api_file)
                self.deadline = defn.module_dict['carbon_deadline_1']
                modules = [self.message_module]
                modules += [m for m in defn.modules if m.flavor == 'lifeline']
                self.lifelines = Cycle(*modules)
                self.lifeline = self.lifelines.current()
                display = defn.config.display
                self.deadline_cv = self.frame.pack(*display.deadline.primary)
                self.lifeline_cv = self.frame.pack(*display.lifeline.primary)
        except Exception as e:
            utils.report_error(e, 'Could not load API file')

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        auto_cycling = prefs.get('auto_cycling')
        self.next_advance = auto_cycling and cctime.get_millis() + auto_cycling

        self.updates_paused_until_millis = cctime.try_isoformat_to_millis(
            prefs, 'updates_paused_until')

        ccui.reset_newsfeed()
        self.message_module.items[:] = [
            ccapi.Item(0, prefs.get('custom_message'), '')
        ]

    def step(self):
        if self.next_advance and cctime.get_millis() > self.next_advance:
            auto_cycling = prefs.get('auto_cycling')
            if auto_cycling:
                self.next_advance += auto_cycling
            else:
                self.next_advance = None
            self.lifeline = self.lifelines.next()
            self.frame.clear()

        self.frame.clear()
        if not self.deadline:
            cv = self.frame.pack(255, 255, 255)
            self.frame.print(1, 0, 'Loading...', 'kairon-10', cv)
        if self.deadline:
            ccui.render_deadline_module(
                self.frame, 0, self.deadline,
                self.deadline_cv, self.app.lang, self.force_caps)
        if self.lifeline:
            ccui.render_lifeline_module(
                self.frame, 16, self.lifeline,
                self.lifeline_cv, self.app.lang, self.force_caps)
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        self.frame.send()

        if cctime.get_millis() > (self.updates_paused_until_millis or 0):
            self.updater.step()

    def receive(self, command, arg=None):
        if command == 'TOGGLE_CAPS':
            self.force_caps = not self.force_caps
            self.frame.clear()
        if command == 'NEXT_LIFELINE':
            self.lifeline = self.lifelines.next()
            self.frame.clear()
        if command == 'SELECTOR':
            delta, value = arg
            if delta > 0:
                self.lifeline = self.lifelines.next()
            else:
                self.lifeline = self.lifelines.previous()
            self.frame.clear()
