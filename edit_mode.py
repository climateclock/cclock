from ccinput import ButtonReader, DialReader, Press
import display
from microfont import small
import prefs

UP_ARROW = '\u2191'

# ASCII characters only, for entering passwords and the like.
ASCII_TEXT_MENU = [
    ('abc', None, UP_ARROW + 'abcdefghijklmnopqrstuvwxyz'),
    ('ABC', None, UP_ARROW + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    ('123', None, UP_ARROW + '1234567890'),
    (',.-!?', None, UP_ARROW + ',.-;:\'!?"@#$%^&*+=_~/\\()[]<>{}'),
    ('\u2423', 'SPACE', ''),
    ('\b', 'BACKSPACE', ''),
    ('\x0b', 'CLEAR', ''),  # we're using Ctrl-K as the clear character
    ('\r', 'ACCEPT', '')
]

# All the common letters and punctuation marks in Western European languages.
DISPLAY_TEXT_MENU = [
    ('abc', None, UP_ARROW + 'abcdefghijklmnopqrstuvwxyz'),
    ('ABC', None, UP_ARROW + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    ('àáâ', None, UP_ARROW + 'àáâãäåæçèéêëìíîïðµñòóôõöøßùúûüýÿþ'),
    ('ÀÁÂ', None, UP_ARROW + 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ'),
    ('+−123', None, UP_ARROW + '+−1234567890²³₂₃₄'),
    (',.-!?', None, UP_ARROW + ',.-;:\'!?¡¿“”@#$%^&*=_~·–—/\\()[]<>{}'),
    ('\u2423', 'SPACE', ''),
    ('\b', 'BACKSPACE', ''),
    ('\x0b', 'CLEAR', ''),
    ('\r', 'ACCEPT', '')
]


class EditMode:
    def __init__(self, app, button_map, dial_map):
        self.app = app
        self.pi = display.get_pi(0x80, 0x80, 0x80)
        self.cursor_pi = display.get_pi(0x00, 0xff, 0x00)

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

        self.menu = ASCII_TEXT_MENU
        self.menu_index = 0
        self.menu_selected = False
        self.char_indexes = [0] * len(self.menu)

    def set_pref(self, pref_title, pref_name, display_text=False):
        self.pref_title = pref_title
        self.pref_name = pref_name
        self.menu = DISPLAY_TEXT_MENU if display_text else ASCII_TEXT_MENU

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.app.bitmap.fill(0)

        small.draw(self.pref_title, self.app.bitmap, 1, 0, self.pi)
        self.text = prefs.get(self.pref_name)
        self.draw_field()
        self.draw_menu()

    def step(self):
        # TODO: Currently every mode's step() method must call display.send()
        # in order for sim_display to detect events; fix this leaky abstraction.
        display.send()

        # Input readers can switch modes, so they should be called last.
        self.reader.step(self.app)
        self.dial_reader.step(self.app)

    # Rows 0 to 9: pref_title and text being edited
    # Row 10: underline cursor for text being edited
    # Rows 11 to 20: group labels
    # Row 21: underline cursor for selected group (okay to reuse row 21,
    #     as this cursor never shows at the same time as character list)
    # Rows 21 to 30: characters in the selected group
    # Row 31: underline cursor for the selected character

    def draw_field(self):
        bitmap = self.app.bitmap
        bitmap.fill(0, 0, 0, None, 11)
        title_width = small.measure(self.pref_title + ': ')
        text_width = small.measure(self.text)

        # Shift text to the left if it's too long to fit.
        text_x = min(title_width, 192 - 5 - text_width)
        cx = small.draw(self.text, bitmap, text_x, 0, self.cursor_pi)
        bitmap.fill(self.cursor_pi, cx, 10, cx + 5, 11)

        bitmap.fill(0, 0, 0, title_width, 11)
        small.draw(self.pref_title + ': ', bitmap, 0, 0, self.pi)

    def draw_menu(self):
        bitmap = self.app.bitmap
        bitmap.fill(0, 0, 11)
        x = 4
        for i, option in enumerate(self.menu):
            label, command, chars = option

            if self.menu_selected and i == self.menu_index:
                x = small.draw(label, bitmap, x, 11, self.cursor_pi)
                small.draw(chars, bitmap, 4, 21, self.pi)
                self.draw_char_cursor()
            else:
                nx = small.draw(label, bitmap, x, 11, self.pi)
                if i == self.menu_index:
                    bitmap.fill(self.cursor_pi, x, 21, nx - 1, 22)
                x = nx
            x += 4

    def draw_char_cursor(self):
        label, command, chars = self.menu[self.menu_index]
        ci = self.char_indexes[self.menu_index]
        left = small.measure(chars[:ci])
        w = small.measure(chars[ci])
        self.app.bitmap.fill(0, 0, 31)
        self.app.bitmap.fill(self.cursor_pi, 4 + left, 31, 3 + left + w, 32)

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
