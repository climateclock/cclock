from ccinput import ButtonReader, DialReader, Press
import cctime
import display
import fs
from microfont import small
import os
import prefs
import utils

LANGS = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'pt': 'Português'
}

class MenuMode:
    def __init__(self, app, button_map, dial_map):
        self.app = app
        self.pi = display.get_pi(0x80, 0x80, 0x80)
        self.cursor_pi = display.get_pi(0x00, 0xff, 0x00)
        self.next_draw = cctime.monotonic_millis()

        self.reader = ButtonReader(button_map, {
            'UP': {
                Press.SHORT: 'PREV_OPTION',
                Press.LONG: 'BACK',
                Press.DOUBLE: 'DUMP_FRAME',
            },
            'DOWN': {
                Press.SHORT: 'NEXT_OPTION',
                Press.LONG: 'GO',
                Press.DOUBLE: 'DUMP_MEMORY',
            },
            'ENTER': {
                Press.SHORT: 'GO',
                Press.LONG: 'BACK',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

        wifi_status = lambda: 'Status: ' + {
            'JOINING': 'Searching',
            'ONLINE': 'Online',
            'CONNECTED': 'Online'
        }.get(self.app.net.state, 'Offline')
        wifi_ssid = lambda: prefs.get('wifi_ssid')
        lifeline_id = lambda: prefs.get('lifeline_id')
        message = lambda: prefs.get('custom_message') or 'None'
        hide_deadline = lambda: (
            prefs.get('hide_deadline') and 'Hidden' or 'Visible')
        language = lambda: LANGS.get(prefs.get('lang', 'en'))

        now = lambda: cctime.millis_to_isoformat(cctime.get_millis())
        battery_level = lambda: app.power_sensor.level
        updater = self.app.clock_mode.updater
        api_fetched = lambda: (updater.api_fetched and
            cctime.millis_to_isoformat(updater.api_fetched) or 'Not yet')
        index_fetched = lambda: (updater.index_fetched and
            cctime.millis_to_isoformat(updater.index_fetched) or 'Not yet')
        versions_present = lambda: ','.join(utils.versions_present() or ['None'])

        def auto_cycling():
            cycling_millis = prefs.get('auto_cycling')
            return cycling_millis and f'{cycling_millis//1000} seconds' or 'Off'

        def auto_update():
            upu = cctime.try_isoformat_to_millis(prefs, 'updates_paused_until')
            min = upu and int((upu - cctime.get_millis())/1000/60)
            return upu and f'Paused {min//60} h {min % 60} min' or 'On'

        # Each node has the form (title, value, command, arg, children).
        self.tree = ('Settings', None, None, None, [
            ('Battery level', battery_level, None, None, []),
            ('Wi-Fi setup', None, None, None, [
                (wifi_status, None, None, None, []),
                ('Network', wifi_ssid, 'WIFI_SSID_MODE', None, []),
                ('Password', None, 'WIFI_PASSWORD_MODE', None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Custom message', message, 'CUSTOM_MESSAGE_MODE', None, []),
            ('Initial lifeline', lifeline_id, None, None, [
                (lifeline.id, None, 'SET_LIFELINE', lifeline.id, [])
                for lifeline in self.app.clock_mode.lifelines.items
            ] + [
                ('Back', None, 'BACK', None, [])
            ]),
            ('Auto cycling', auto_cycling, None, None, [
                ('Off', None, 'SET_CYCLING', 0, []),
                ('10 seconds', None, 'SET_CYCLING', 10000, []),
                ('15 seconds', None, 'SET_CYCLING', 15000, []),
                ('30 seconds', None, 'SET_CYCLING', 30000, []),
                ('60 seconds', None, 'SET_CYCLING', 60000, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Auto update', auto_update, None, None, [
                ('On', None, 'SET_UPDATES_PAUSED', None, []),
                ('Pause for 4 hours', None,
                    'SET_UPDATES_PAUSED', 4*3600*1000, []),
                ('Pause for 24 hours', None,
                    'SET_UPDATES_PAUSED', 24*3600*1000, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Deadline', hide_deadline, None, None, [
                ('Visible', None, 'SET_HIDE_DEADLINE', False, []),
                ('Hidden', None, 'SET_HIDE_DEADLINE', True, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Language', language, None, None, [
                (LANGS[lang], None, 'SET_LANG', lang, []) for lang in LANGS
            ] + [
                ('Back', None, 'BACK', None, [])
            ]),
            ('System info', None, None, None, [
                (f'Time', now, None, None, []),
                (f'MAC ID', self.app.net.mac_address, None, None, []),
                (f'Version', utils.version_dir, None, None, []),
                (f'Versions present', versions_present, None, None, []),
                (f'Last API fetch', lambda: cctime.millis_to_isoformat(
                    updater.api_fetched), None, None, []),
                (f'Last update fetch', lambda: cctime.millis_to_isoformat(
                    updater.index_fetched), None, None, []),
                (f'Firmware', os.uname().version, None, None, []),
                (f'ESP firmware', self.app.net.firmware_version,
                    None, None, []),
                (f'Free disk', lambda: f'{fs.free()//1000} kB', None, None, []),
                (f'Free memory', utils.free, None, None, []),
                (f'Uptime', self.app.frame_counter.uptime, None, None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Back', None, 'CLOCK_MODE', None, [])
        ])
        self.crumbs = []
        self.node = self.tree
        self.top = self.index = self.offset = 0

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.draw()

    def proceed(self, node):
        title, value, command, arg, children = node
        if command:
            self.app.receive(command, arg)
        else:
            if self.node:
                self.crumbs.append((self.node, self.top, self.index))
            self.node = node
            self.top = self.index = self.offset = 0
            self.draw()

    def format_title(self, title, value):
        if title and callable(title):
            title = title()
        if value:
            if callable(value):
                value = value()
            return f'{title}: {value}'
        return title

    def draw(self):
        title, value, command, arg, children = self.node
        title = self.format_title(title, not children and value)

        bitmap = self.app.bitmap
        bitmap.fill(0)
        small.draw(title, bitmap, 1 - self.offset, 0, self.pi)
        y = 0
        for index in range(self.top, self.top + 3):
            if index >= len(children):
                break
            child_title, child_value, _, _, _ = children[index]
            child_title = self.format_title(child_title, child_value)
            small.draw(child_title, bitmap, 65, y, self.pi)
            if index == self.index:
                small.draw('>', bitmap, 59, y, self.cursor_pi)
            y += 11
        display.send()

    def step(self):
        if cctime.monotonic_millis() > self.next_draw:
            self.draw()
            self.next_draw += 20

        # Input readers can switch modes, so they should be called last.
        self.reader.step(self.app)
        self.dial_reader.step(self.app)

    def receive(self, command, arg=None):
        if command == 'SELECTOR':
            delta, value = arg
            self.move_cursor(delta)
        if command == 'PREV_OPTION':
            self.move_cursor(-1)
        if command == 'NEXT_OPTION':
            self.move_cursor(1)
        if command == 'SET_LIFELINE':
            prefs.set('lifeline_id', arg)
            command = 'BACK'
        if command == 'SET_HIDE_DEADLINE':
            prefs.set('hide_deadline', arg)
            command = 'BACK'
        if command == 'SET_CYCLING':
            prefs.set('auto_cycling', arg)
            command = 'BACK'
        if command == 'SET_UPDATES_PAUSED':
            if arg:
                prefs.set('updates_paused_until',
                    cctime.millis_to_isoformat(cctime.get_millis() + arg))
            else:
                prefs.set('updates_paused_until', None)
            command = 'BACK'
        if command == 'SET_LANG':
            prefs.set('lang', arg)
            command = 'BACK'
        if command == 'GO':
            title, value, command, arg, children = self.node
            if children:
                self.proceed(children[self.index])
            else:
                command = 'BACK'
        if command == 'BACK':
            if self.crumbs:
                self.node, self.top, self.index = self.crumbs.pop()
                self.offset = 0
                self.draw()
            else:
                self.app.receive('CLOCK_MODE')

    def move_cursor(self, delta):
        title, value, command, arg, children = self.node
        if children:
            self.index = max(0, min(len(children) - 1, self.index + delta))
            self.top = max(self.index - 2, min(self.index, self.top))
            print(f'Cursor moved to {repr(children[self.index][0])}')
        else:
            self.offset = max(0, self.offset + delta * 12)
        self.draw()



