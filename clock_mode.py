import ccapi
from ccinput import ButtonReader, DialReader, Press
import cctime
import ccui
import display
import fs
from microfont import small
import prefs
from updater import SoftwareUpdater
import utils


class ClockMode:
    def __init__(self, app, net, button_map, dial_map):
        self.app = app

        self.deadline = None
        self.lifeline = None
        self.lifelines = None
        self.message_module = ccapi.Newsfeed(
            'custom_message', 'newsfeed', 'lifeline', [], [])

        self.reload_definition()
        self.updater = SoftwareUpdater(app, net, self)
        utils.log('Created SoftwareUpdater')

        self.reader = ButtonReader(button_map, {
            'UP': {
                Press.SHORT: 'NEXT_LANGUAGE',
                Press.DOUBLE: 'DUMP_FRAME',
            },
            'DOWN': {
                Press.SHORT: 'NEXT_LIFELINE',
                Press.LONG: 'MENU_MODE',
                Press.DOUBLE: 'DUMP_MEMORY',
            },
            'ENTER': {
                Press.SHORT: 'MENU_MODE',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

    def reload_definition(self):
        utils.log()
        try:
            with fs.open('/data/clock.json') as api_file:
                defn = ccapi.load(api_file)
                defn.module_dict['custom_message'] = self.message_module
                defn.modules.append(self.message_module)
                deadlines = [m for m in defn.modules if m.flavor == 'deadline']
                lifelines = [m for m in defn.modules if m.flavor == 'lifeline']

                self.deadline = deadlines and deadlines[0] or None
                self.lifelines = utils.Cycle(*lifelines)

                current = defn.module_dict.get(prefs.get('lifeline_id'))
                if current in lifelines:
                    while self.lifelines.get(1) != current:
                        pass
                self.switch_lifeline(0)

                self.deadline_pi = display.get_pi(
                    *defn.config.display.deadline.primary)
                self.lifeline_pi = display.get_pi(
                    *defn.config.display.lifeline.primary)
        except Exception as e:
            utils.report_error(e, 'Could not load API file')
        utils.log('reload_definition')

    def switch_lifeline(self, delta):
        if self.lifelines:
            self.lifeline = self.lifelines.get(delta)
            if self.lifeline == self.message_module:
                if not prefs.get('custom_message'):
                    self.lifeline = self.lifelines.get(delta or 1)
            prefs.set('lifeline_id', self.lifeline.id)
            self.app.bitmap.fill(0)

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.app.bitmap.fill(0)

        self.next_advance = None
        auto_cycling = prefs.get('auto_cycling')
        if auto_cycling:
            self.next_advance = cctime.monotonic_millis() + auto_cycling

        self.updates_paused_until_millis = cctime.try_isoformat_to_millis(
            prefs, 'updates_paused_until')

        ccui.reset_newsfeed()
        self.message_module.items[:] = [
            ccapi.Item(0, prefs.get('custom_message'), '')
        ]
        self.switch_lifeline(0)

    def step(self):
        if self.next_advance and cctime.monotonic_millis() > self.next_advance:
            auto_cycling = prefs.get('auto_cycling')
            if auto_cycling:
                self.next_advance += auto_cycling
            else:
                self.next_advance = None
            self.switch_lifeline(1)

        bitmap = self.app.bitmap
        bitmap.fill(0)
        if not (self.deadline or self.lifelines):
            pi = display.get_pi(0x80, 0x80, 0x80)
            ssid = prefs.get('wifi_ssid')
            small.draw(f'Joining Wi-Fi network "{ssid}"...', bitmap, 1, 0, pi)
        if self.deadline:
            ccui.render_deadline_module(
                bitmap, 0, self.deadline,
                self.deadline_pi, self.app.lang)
        if self.lifeline:
            ccui.render_lifeline_module(
                bitmap, 16, self.lifeline,
                self.lifeline_pi, self.app.lang)
        display.send()
        if cctime.get_millis() > (self.updates_paused_until_millis or 0):
            self.updater.step()

        # Input readers can switch modes, so they should be called last.
        self.reader.step(self.app)
        self.dial_reader.step(self.app)

    def receive(self, command, arg=None):
        if command == 'NEXT_LIFELINE':
            self.switch_lifeline(1)
        if command == 'SELECTOR':
            delta, value = arg
            self.switch_lifeline(delta > 0 and 1 or -1)
