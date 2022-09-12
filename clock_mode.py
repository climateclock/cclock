import ccapi
from ccinput import ButtonReader, DialReader, Press
import cctime
import ccui
import fs
from mode import Mode
import prefs
from updater import SoftwareUpdater
import utils
from utils import Cycle, log


class ClockMode(Mode):
    def __init__(self, app, network, button_map, dial_map):
        log('Starting ClockMode.__init__')
        super().__init__(app)
        self.network = network

        self.deadline = None
        self.lifeline = None
        self.lifelines = None
        self.message_module = ccapi.Newsfeed(
            'custom_message', 'newsfeed', 'lifeline', [], [])

        self.reload_definition()
        self.updater = SoftwareUpdater(app, network, self)
        log('Created SoftwareUpdater')

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
                Press.SHORT: 'MENU_MODE',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)
        self.force_caps = False
        log('Finished ClockMode.__init__')

    def reload_definition(self):
        log()
        try:
            with fs.open('/cache/clock.json') as api_file:
                defn = ccapi.load(api_file)
                defn.module_dict['custom_message'] = self.message_module
                defn.modules.append(self.message_module)
                deadlines = [m for m in defn.modules if m.flavor == 'deadline']
                lifelines = [m for m in defn.modules if m.flavor == 'lifeline']

                self.deadline = deadlines and deadlines[0] or None
                self.lifelines = Cycle(*lifelines)

                current = defn.module_dict.get(prefs.get('lifeline_id'))
                if current in lifelines:
                    while self.lifelines.get(1) != current:
                        pass
                self.switch_lifeline(0)

                display = defn.config.display
                self.deadline_cv = self.frame.pack(*display.deadline.primary)
                self.lifeline_cv = self.frame.pack(*display.lifeline.primary)
        except Exception as e:
            utils.report_error(e, 'Could not load API file')
        log('reload_definition')

    def switch_lifeline(self, delta):
        if self.lifelines:
            self.lifeline = self.lifelines.get(delta)
            if self.lifeline == self.message_module:
                if not prefs.get('custom_message'):
                    self.lifeline = self.lifelines.get(delta or 1)
            prefs.set('lifeline_id', self.lifeline.id)
            self.frame.clear()

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
        self.switch_lifeline(0)

    def step(self):
        if self.next_advance and cctime.get_millis() > self.next_advance:
            auto_cycling = prefs.get('auto_cycling')
            if auto_cycling:
                self.next_advance += auto_cycling
            else:
                self.next_advance = None
            self.switch_lifeline(1)

        self.frame.clear()
        if not (self.deadline or self.lifelines):
            cv = self.frame.pack(255, 255, 255)
            ssid = prefs.get('wifi_ssid')
            self.frame.print(1, 0, f'Joining Wi-Fi network "{ssid}"...', 'kairon-10', cv)
        if self.deadline:
            ccui.render_deadline_module(
                self.frame, 0, self.deadline,
                self.deadline_cv, self.app.lang, self.force_caps)
        if self.lifeline:
            ccui.render_lifeline_module(
                self.frame, 16, self.lifeline,
                self.lifeline_cv, self.app.lang, self.force_caps)
        self.frame.send()
        if cctime.get_millis() > (self.updates_paused_until_millis or 0):
            self.updater.step()

        # Handle input at the end of step(), because it might change modes.
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)

    def receive(self, command, arg=None):
        if command == 'TOGGLE_CAPS':
            self.force_caps = not self.force_caps
            self.frame.clear()
        if command == 'NEXT_LIFELINE':
            self.switch_lifeline(1)
        if command == 'SELECTOR':
            delta, value = arg
            self.switch_lifeline(delta > 0 and 1 or -1)
