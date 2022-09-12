from ccinput import ButtonReader, DialReader, Press
from mode import Mode
import prefs

FONT = 'kairon-10'
UP_ARROW = '\u2191'

# ASCII characters only, for entering passwords and the like.
ASCII_TEXT_ENTRY_MENU = [
    ('abc', None, UP_ARROW + 'abcdefghijklmnopqrstuvwxyz'),
    ('ABC', None, UP_ARROW + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    ('123', None, UP_ARROW + '1234567890'),
    (',.!?', None, UP_ARROW + ',.;:!?-\'"@#$%^&*+=_~/\\()[]<>{}'),
    ('\u2423', 'SPACE', ''),
    ('\b', 'BACKSPACE', ''),
    ('\x0b', 'CLEAR', ''),  # we're using Ctrl-K as the clear character
    ('\r', 'ACCEPT', '')
]

# All the common letters and punctuation marks in Western European languages.
DISPLAY_TEXT_ENTRY_MENU = [
    ('abc', None, UP_ARROW + 'abcdefghijklmnopqrstuvwxyz'),
    ('ABC', None, UP_ARROW + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    ('ÀÁÂ', None, UP_ARROW + 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ'),
    ('àáâ', None, UP_ARROW + 'àáâãäåæçèéêëìíîïðµñòóôõöøßùúûüýÿþ'),
    ('+−123', None, UP_ARROW + '+−1234567890²³₂₃₄'),
    ('-\',.!?', None, UP_ARROW + '-\',.;:!?¡¿"‘’“”@#$%^&*=_~/\\()[]<>«»{}'),
    ('\u2423', 'SPACE', ''),
    ('\b', 'BACKSPACE', ''),
    ('\x0b', 'CLEAR', ''),
    ('\r', 'ACCEPT', '')
]


class PrefEntryMode(Mode):
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

        self.menu = ASCII_TEXT_ENTRY_MENU
        self.menu_index = 0
        self.menu_selected = False
        self.char_indexes = [0] * len(self.menu)

    def set_pref(self, pref_title, pref_name):
        self.pref_title = pref_title
        self.pref_name = pref_name

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()

        self.frame.print(1, 0, self.pref_title, FONT, cv=self.cv)
        self.text = prefs.get(self.pref_name)
        self.draw_field()
        self.draw_menu()

    def step(self):
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()
        # Handle input at the end of step(), because it might change modes.
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)

    # Rows 0 to 9: pref_title and text being edited
    # Row 10: underline cursor for text being edited
    # Rows 11 to 20: group labels
    # Row 21: underline cursor for selected group (okay to reuse row 21,
    #     as this cursor never shows at the same time as character list)
    # Rows 21 to 30: characters in the selected group
    # Row 31: underline cursor for the selected character

    def draw_field(self):
        self.frame.clear(0, 0, None, 11)
        x = self.frame.print(0, 0, self.pref_title + ': ', FONT, cv=self.cv)
        x = self.frame.print(x, 0, self.text, FONT, cv=self.cursor_cv)
        self.frame.fill(x, 10, 5, 1, cv=self.cursor_cv)

    def draw_menu(self):
        self.frame.clear(0, 11)
        x = 5
        for i, option in enumerate(self.menu):
            label, command, chars = option

            if self.menu_selected and i == self.menu_index:
                x = self.frame.print(x, 11, label, FONT, cv=self.cursor_cv)
                self.frame.print(5, 21, chars, FONT, cv=self.cv)
                self.draw_char_cursor()
            else:
                nx = self.frame.print(x, 11, label, FONT, cv=self.cv)
                if i == self.menu_index:
                    self.frame.fill(x, 21, nx - x - 1, 1, cv=self.cursor_cv)
                x = nx
            x += 4

    def draw_char_cursor(self):
        label, command, chars = self.menu[self.menu_index]
        ci = self.char_indexes[self.menu_index]
        left = self.frame.measure(chars[:ci], FONT)
        w = self.frame.measure(chars[ci], FONT)
        self.frame.clear(0, 31)
        self.frame.fill(5 + left, 31, w - 1, 1, cv=self.cursor_cv)

    def receive(self, command, arg=None):
        if self.menu_selected:
            move_cursor = self.move_char_cursor
        else:
            move_cursor = self.move_menu_cursor
        if command == 'SELECTOR':
            delta, value = arg
            move_cursor(delta)
        if command == 'PREV_OPTION':
            move_cursor(-1)
        if command == 'NEXT_OPTION':
            move_cursor(1)

        if command == 'GO':
            label, command, chars = self.menu[self.menu_index]
            if self.menu_selected:
                ci = self.char_indexes[self.menu_index]
                if ci == 0:
                    self.menu_selected = False
                else:
                    self.text += chars[ci]
                    self.draw_field()
            elif not command:
                self.menu_selected = True
            self.draw_menu()
            # Fall through to handle the new value of command

        if command == 'BACK':
            if self.menu_selected:
                self.menu_selected = False
                self.draw_menu()
            else:
                self.app.receive('MENU_MODE')
        if command == 'SPACE':
            self.text += ' '
            self.draw_field()
        if command == 'BACKSPACE':
            print('%r' % self.text)
            self.text = self.text[:-1]
            print('-> %r' % self.text)
            self.draw_field()
        if command == 'CLEAR':
            self.text = ''
            self.draw_field()

        if command == 'ACCEPT':
            prefs.set(self.pref_name, self.text)
            self.app.receive('MENU_MODE')

    def move_menu_cursor(self, delta):
        self.menu_index = max(0, min(len(self.menu) - 1, self.menu_index + delta))
        self.draw_menu()

    def move_char_cursor(self, delta):
        label, command, chars = self.menu[self.menu_index]
        ci = self.char_indexes[self.menu_index]
        self.char_indexes[self.menu_index] = max(0, min(len(chars) - 1, ci + delta))
        self.draw_char_cursor()
