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
        self.start_millis = cctime.get_millis()

        self.deadline = None
        self.module = None
        self.modules = None
        self.custom_message = ccapi.Newsfeed(
            'custom_message', 'newsfeed', 'lifeline', [], [], [])

        self.langs = {}
        self.load_definition()
        self.updater = SoftwareUpdater(app, net, self)
        utils.log('Created SoftwareUpdater')

        self.reader = ButtonReader(button_map, {
            'UP': {
                Press.DOUBLE: 'DUMP_FRAME',
            },
            'DOWN': {
                Press.SHORT: 'NEXT_MODULE',
                Press.LONG: 'MENU_MODE',
                Press.DOUBLE: 'DUMP_MEMORY',
            },
            'ENTER': {
                Press.SHORT: 'MENU_MODE',
                Press.REPEAT: 'LOCK_TICK',
                Press.RELEASE: 'LOCK_END',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)
        self.low_battery_cv = display.get_pi(0xff, 0, 0)

    def load_definition(self):
        lang = prefs.get('lang', 'en')
        if self.load_path(f'data/clock.{lang}.json'):
            return
        if self.load_path(f'clock.{lang}.json'):
            return
        if self.load_path('data/clock.json'):
            return
        if self.load_path('clock.json'):
            return

    def load_path(self, path):
        try:
            with fs.open(path) as api_file:
                defn = ccapi.load(api_file)
            disp = defn.config.display
            self.deadline_pi = display.get_pi(*disp.deadline.primary)
            self.lifeline_pi = display.get_pi(*disp.lifeline.primary)
            self.langs = defn.config.langs

            for m in defn.modules:
                if m.flavor == 'deadline':
                    self.deadline = m

            self.modules = utils.Cycle(defn.modules + [self.custom_message])
            module_id = self.module and self.module.id or prefs.get('module_id')
            self.advance_module(id=module_id)
            utils.log(f'Loaded {path}')
            return True
        except Exception as e:
            print(e)

    def advance_module(self, delta=0, id=None):
        if delta:
            self.start_millis = cctime.get_millis()

        # Validate the inputs
        if not self.modules or len(self.modules.items) <= 2:
            return  # definition not yet loaded, or has no lifelines

        # Advance in the specified direction, skipping modules we can't display
        original_id = self.modules.advance(0).id
        m = self.modules.advance(delta)
        while (
            m == self.deadline and prefs.get('display_mode') == 'DUAL' or
            m == self.custom_message and not prefs.get('custom_message') or
            id and m.id != id
        ):
            m = self.modules.advance(delta or 1)
            if m.id == original_id:  # didn't find a displayable module
                break
        self.module = m

        # Render static parts of the display
        self.app.bitmap.fill(0)
        if prefs.get('display_mode') != 'DUAL':
            ccui.render_label(
                self.app.bitmap, 16,
                self.module.full_width_labels or self.module.labels,
                self.deadline_pi if m == self.deadline else self.lifeline_pi
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
        self.custom_message.items[:] = [
            ccapi.Item(0, prefs.get('custom_message'), '')
        ]
        self.advance_module(0)

    def step(self):
        if self.next_advance and cctime.monotonic_millis() > self.next_advance:
            auto_cycling = prefs.get('auto_cycling')
            if auto_cycling and not self.app.locked:
                self.next_advance += auto_cycling
                self.advance_module(1)
            else:
                self.next_advance = None

        bitmap = self.app.bitmap
        dual_mode = prefs.get('display_mode') == 'DUAL'

        if self.module == self.deadline or dual_mode:
            ccui.render_module(bitmap, 0, self.deadline, self.deadline_pi)

        pi = self.deadline_pi if self.module.id[:1] == '_' else self.lifeline_pi
        if self.module != self.deadline:
            y = dual_mode*16
            ccui.render_module(
                bitmap, y, self.module, pi, dual_mode, self.start_millis)

        if self.app.lock_tick > 0:
            if self.app.lock_tick < 6:
                text = 'Unlocking' if self.app.locked else 'Locking'
                text += '.'*self.app.lock_tick
            else:
                text = 'Display is '
                text += 'locked.' if self.app.locked else 'unlocked.'
            bitmap.fill(0, 0, 0, small.measure(text) + 1, small.h + 1)
            small.draw(text, bitmap, 1, 0)

        level = self.app.battery_sensor.level
        if level is not None and level < 10:
            blink = cctime.monotonic_millis() % 1500
            bitmap.fill(self.low_battery_cv * (blink < 1000), 190, 30, 192, 32)

        display.send()
        if cctime.get_millis() > (self.updates_paused_until_millis or 0):
            if not self.app.locked:
                self.updater.step()

        # Input readers can switch modes, so they should be called last.
        self.reader.step(self.app)
        self.dial_reader.step(self.app)

    def receive(self, command, arg=None):
        if command == 'NEXT_MODULE':
            self.advance_module(1)
        if command == 'SELECTOR':
            delta, value = arg
            self.advance_module(delta > 0 and 1 or -1)
