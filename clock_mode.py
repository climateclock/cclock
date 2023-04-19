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
        self.lifeline_ids = None
        self.lifelines = None
        self.hide_deadline = False
        self.custom_message_module = ccapi.Newsfeed(
            'custom_message', 'newsfeed', 'lifeline', [], [], [])

        self.load_definition()
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

    def load_definition(self):
        utils.log()
        try:
            self.load_path('data/clock.json')
        except Exception as e:
            print(f'Could not load /data/clock.json: {e}')
            try:
                self.load_path('clock.json')
            except Exception as e:
                print(f'Could not load /clock.json: {e}')

    def load_path(self, path):
        with fs.open(path) as api_file:
            defn = ccapi.load(api_file)

            deadlines = []
            self.lifeline_ids = []
            lifelines = []
            lifeline_index = 0
            for m in defn.modules:
                if m.flavor == 'deadline':
                    deadlines.append(m)
                if m.flavor == 'lifeline':
                    self.lifeline_ids.append(m.id)
                    if m.id == prefs.get('lifeline_id'):
                        lifeline_index = len(lifelines)
                    if m.labels or m.full_width_labels:
                        lifelines.append((m, True))
                    lifelines.append((m, False))
            lifelines.append((self.custom_message_module, False))

            self.deadline = deadlines and deadlines[0] or None
            self.lifelines = utils.Cycle(lifelines)
            self.deadline_pi = display.get_pi(
                *defn.config.display.deadline.primary)
            self.lifeline_pi = display.get_pi(
                *defn.config.display.lifeline.primary)

            self.advance_lifeline(lifeline_index)
            if self.hide_deadline and not prefs.get('hide_deadline'):
                self.advance_lifeline(1)

        utils.log(f'Loaded {path}')

    def advance_lifeline(self, delta):
        if self.lifelines:
            self.lifeline, self.hide_deadline = self.lifelines.get(delta)
            if (self.lifeline == self.custom_message_module and
                not prefs.get('custom_message')):
                self.lifeline, self.hide_deadline = self.lifelines.get(delta or 1)
            self.app.bitmap.fill(0)
            if self.hide_deadline:
                ccui.render_label(
                    self.app.bitmap, 16,
                    self.lifeline.full_width_labels or self.lifeline.labels,
                    self.lifeline_pi
                )

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
        self.custom_message_module.items[:] = [
            ccapi.Item(0, prefs.get('custom_message'), '')
        ]
        self.advance_lifeline(0)

    def step(self):
        if self.next_advance and cctime.monotonic_millis() > self.next_advance:
            auto_cycling = prefs.get('auto_cycling')
            if auto_cycling:
                self.next_advance += auto_cycling
            else:
                self.next_advance = None
            self.advance_lifeline(1)

        bitmap = self.app.bitmap
        if self.hide_deadline:
            if self.lifeline:
                ccui.render_lifeline_module(
                    bitmap, 0, self.lifeline,
                    self.deadline_pi if self.lifeline.id[:1] == '_'
                    else self.lifeline_pi, False, self.app.lang)
        else:
            if self.deadline:
                ccui.render_deadline_module(
                    bitmap, 0, self.deadline,
                    self.deadline_pi, self.app.lang)
            if self.lifeline:
                ccui.render_lifeline_module(
                    bitmap, 16, self.lifeline,
                    self.lifeline_pi, True, self.app.lang)
        display.send()
        if cctime.get_millis() > (self.updates_paused_until_millis or 0):
            self.updater.step()

        # Input readers can switch modes, so they should be called last.
        self.reader.step(self.app)
        self.dial_reader.step(self.app)

    def receive(self, command, arg=None):
        if command == 'NEXT_LIFELINE':
            self.advance_lifeline(1)
        if command == 'SELECTOR':
            delta, value = arg
            self.advance_lifeline(delta > 0 and 1 or -1)
