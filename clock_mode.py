import ccapi
from ccinput import ButtonReader, Press
import cctime
import ccui
from mode import Mode
from updater import SoftwareUpdater
import utils
from utils import Cycle


class ClockMode(Mode):
    def __init__(self, app, fs, network, button_map):
        super().__init__(app)
        self.fs = fs
        self.network = network

        self.updater = SoftwareUpdater(fs, network, app.prefs, self)
        self.deadline = None
        self.lifeline = None
        self.message_module = ccapi.Newsfeed()
        self.message_module.type = 'newsfeed'
        self.message_module.items = [ccapi.NewsfeedItem()]

        self.reload_definition()

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

    def reload_definition(self):
        try:
            with self.fs.open('/cache/clock.json') as api_file:
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
        self.frame.clear()
        sec = self.app.prefs.get('auto_cycling_sec')
        self.next_advance = sec and cctime.monotonic() + sec

        ccui.reset_newsfeed()
        item = self.message_module.items[0]
        item.headline = self.app.prefs.get('custom_message')
        item.source = ''

    def step(self):
        if self.next_advance and cctime.monotonic() > self.next_advance:
            sec = self.app.prefs.get('auto_cycling_sec')
            if sec:
                self.next_advance += sec
            self.lifeline = self.lifelines.next()
            self.frame.clear()

        self.frame.clear()
        if not self.deadline:
            self.frame.print(1, 0, 'Loading...', 'kairon-10', self.deadline_cv)
        if self.deadline:
            ccui.render_deadline_module(
                self.frame, 0, self.deadline,
                self.deadline_cv, self.app.lang, self.force_caps)
        if self.lifeline:
            ccui.render_lifeline_module(
                self.frame, 16, self.lifeline,
                self.lifeline_cv, self.app.lang, self.force_caps)
        self.reader.step(self.app.receive)
        self.frame.send()
        self.updater.step()

    def receive(self, command, arg=None):
        if command == 'TOGGLE_CAPS':
            self.force_caps = not self.force_caps
            self.frame.clear()
        if command == 'NEXT_LIFELINE':
            self.lifeline = self.lifelines.next()
            self.frame.clear()
