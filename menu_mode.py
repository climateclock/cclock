from ccinput import ButtonReader, DialReader, Press
import cctime
from mode import Mode
from network import State
import prefs
import sys

FONT = 'kairon-10'


class MenuMode(Mode):
    def __init__(self, app, button_map, dial_map):
        super().__init__(app)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'PREV_OPTION',
                Press.LONG: 'BACK',
                Press.DOUBLE: 'DUMP_FRAME',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_OPTION',
                Press.LONG: 'GO',
                Press.DOUBLE: 'DUMP_MEMORY',
            },
            button_map['ENTER']: {
                Press.SHORT: 'GO',
                Press.LONG: 'BACK',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

        wifi_status = lambda: 'Status: ' + ['Online', 'Offline'][self.app.network.state == State.OFFLINE]
        wifi_ssid = lambda: prefs.get('wifi_ssid')
        updater = self.app.clock_mode.updater
        index_updated = lambda: updater.index_updated or 'None'
        index_fetched = lambda: updater.index_fetched and cctime.millis_to_isoformat(updater.index_fetched) or 'Not yet'
        software_version = sys.path[0]
        esp_firmware_version = self.app.network.get_firmware_version()
        esp_hardware_address = self.app.network.get_hardware_address()
        now = lambda: cctime.millis_to_isoformat(cctime.get_millis())

        def auto_cycling():
            cycling_millis = prefs.get('auto_cycling')
            return cycling_millis and f'{cycling_millis//1000} seconds' or 'Off'

        def auto_update():
            upu = cctime.try_isoformat_to_millis(prefs, 'updates_paused_until')
            min = upu and int((upu - cctime.get_millis())/1000/60)
            return upu and f'Paused {min//60} h {min % 60} min' or 'On'

        # Each node has the form (title, value, command, arg, children).
        self.tree = ('Settings', None, None, None, [
            ('Wi-Fi setup', None, None, None, [
                (wifi_status, None, None, None, []),
                ('Network', wifi_ssid, 'WIFI_SSID_MODE', None, []),
                ('Password', None, 'WIFI_PASSWORD_MODE', None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            (f'Auto cycling', auto_cycling, None, None, [
                ('Off', None, 'SET_CYCLING', 0, []),
                ('15 seconds', None, 'SET_CYCLING', 15000, []),
                ('60 seconds', None, 'SET_CYCLING', 60000, []),
                ('Back', None, 'BACK', None, [])
            ]),
            (f'Auto update', auto_update, None, None, [
                ('On', None, 'SET_UPDATES_PAUSED', None, []),
                ('Pause for 4 hours', None, 'SET_UPDATES_PAUSED', 4*3600*1000, []),
                ('Pause for 24 hours', None, 'SET_UPDATES_PAUSED', 24*3600*1000, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Custom message', None, 'CUSTOM_MESSAGE_MODE', None, []),
            ('System info', None, None, None, [
                (updater.index_name or 'Climate Clock', None, None, None, []),
                (f'Version', software_version, None, None, []),
                (f'Time', now, None, None, []),
                (f'Index version', index_updated, None, None, []),
                (f'Index fetched', index_fetched, None, None, []),
                (f'ESP firmware', esp_firmware_version, None, None, []),
                (f'MAC ID', esp_hardware_address, None, None, []),
                ('Back', None, 'BACK', None, [])
            ]),
            ('Exit', None, 'CLOCK_MODE', None, [])
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
        if value and callable(value):
            value = value()
        return value and f'{title}: {value}' or title

    def draw(self):
        title, value, command, arg, children = self.node
        title = self.format_title(title, not children and value)

        self.frame.clear()
        self.frame.print(1 - self.offset, 0, title, FONT, cv=self.cv)
        y = 0
        for index in range(self.top, self.top + 3):
            if index >= len(children):
                break
            child_title, child_value, _, _, _ = children[index]
            child_title = self.format_title(child_title, child_value)
            self.frame.print(64, y, child_title, FONT, cv=self.cv)
            if index == self.index:
                self.frame.print(58, y, '>', FONT, cv=self.cursor_cv)
            y += 11
        self.frame.send()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def receive(self, command, arg=None):
        if command == 'SELECTOR':
            delta, value = arg
            self.move_cursor(delta)
        if command == 'PREV_OPTION':
            self.move_cursor(-1)
        if command == 'NEXT_OPTION':
            self.move_cursor(1)
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
        else:
            self.offset = max(0, self.offset + delta * 12)
        self.draw()



