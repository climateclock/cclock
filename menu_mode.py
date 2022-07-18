from ccinput import ButtonReader, DialReader, Press
import cctime
from mode import Mode
import sys


class MenuMode(Mode):
    def __init__(self, app, button_map, dial_map):
        super().__init__(app)
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.cursor_label = self.frame.new_label('>', 'kairon-10')

        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'PREV_OPTION',
                Press.LONG: 'BACK',
            },
            button_map['DOWN']: {
                Press.SHORT: 'NEXT_OPTION',
                Press.LONG: 'PROCEED',
            },
            button_map['ENTER']: {
                Press.SHORT: 'PROCEED',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        wifi_ssid = self.app.prefs.get('wifi_ssid')
        updater = self.app.updater
        index_fetched = updater.index_fetched and updater.index_fetched.isoformat()
        software_version = sys.path[0]
        firmware_version = self.app.network.get_firmware_version()
        hardware_address = self.app.network.get_hardware_address()
        sec = self.app.prefs.get('auto_cycling_sec')
        auto_cycling = sec and f'{sec} seconds' or 'Off'
        self.tree = ('Settings', None, [
            ('Wi-Fi setup', None, [
                ('Network: ' + wifi_ssid, ('WIFI_SSID_MODE', None), []),
                ('Password', ('WIFI_PASSWORD_MODE', None), []),
                ('Back', ('BACK', None), [])
            ]),
            (f'Auto cycling: {auto_cycling}', None, [
                ('Off', ('SET_CYCLING', 0), []),
                ('15 seconds', ('SET_CYCLING', 15), []),
                ('60 seconds', ('SET_CYCLING', 60), []),
                ('Back', ('BACK', None), [])
            ]),
            ('System info', None, [
                (updater.index_name or 'Climate Clock', None, []),
                (f'Version: {software_version}', None, []),
                (f'Time: {cctime.get_datetime().isoformat()}', None, []),
                (f'Index version: {updater.index_updated}', None, []),
                (f'Index fetched: {updater.index_fetched}', None, []),
                (f'ESP firmware: {firmware_version}', None, []),
                (f'MAC ID: {hardware_address}', None, []),
                ('Back', ('BACK', None), [])
            ]),
            ('Exit', ('CLOCK_MODE', None), [])
        ])
        self.crumbs = []
        self.top = self.index = self.offset = 0
        self.proceed(self.tree)

    def proceed(self, node):
        title, command_arg, children = node
        if command_arg:
            self.app.receive(*command_arg)
        else:
            self.crumbs.append((node, self.top, self.index))
            self.top = self.index = self.offset = 0
            self.draw()

    def draw(self):
        (title, command, children), _, _ = self.crumbs[-1]
        self.frame.clear()
        label = self.frame.new_label(title, 'kairon-10')
        self.frame.paste(1 - self.offset, 0, label, cv=self.cv)
        y = 0
        for index in range(self.top, self.top + 3):
            if index >= len(children):
                break
            child = children[index]
            label = self.frame.new_label(child[0], 'kairon-10')
            self.frame.paste(64, y, label, cv=self.cv)
            if index == self.index:
                self.frame.paste(58, y, self.cursor_label, cv=self.cursor_cv)
            y += 11

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
            self.app.prefs.set('auto_cycling_sec', arg)
            self.app.receive('MENU_MODE')  # reformat the menu strings
        if command == 'PROCEED':
            (title, command_arg, children), _, _ = self.crumbs[-1]
            if children:
                self.proceed(children[self.index])
            else:
                command = 'BACK'
        if command == 'BACK':
            _, self.top, self.index = self.crumbs.pop()
            self.offset = 0
            self.draw()

    def move_cursor(self, delta):
        (title, command, children), _, _ = self.crumbs[-1]
        if children:
            self.index = max(0, min(len(children) - 1, self.index + delta))
            self.top = max(self.index - 2, min(self.index, self.top))
        else:
            self.offset = max(0, self.offset + delta * 12)
        self.draw()



