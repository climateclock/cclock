from ccinput import ButtonReader, DialReader, Press
from mode import Mode

FONT = 'kairon-10'
UP_ARROW = '\u2191'

# ASCII characters only, for entering passwords and the like.
ASCII_TEXT_ENTRY_MENU = [
    ('abc', None, UP_ARROW + 'abcdefghijklmnopqrstuvwxyz'),
    ('ABC', None, UP_ARROW + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
    ('123', None, UP_ARROW + '1234567890'),
    (',.!?', None, UP_ARROW + ',.;:!?-\'"@#$%^&*+=_~/\\()[]<>{}'),
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
    ('\b', 'BACKSPACE', ''),
    ('\x0b', 'CLEAR', ''),
    ('\r', 'ACCEPT', '')
]


class PrefEntryMode(Mode):
    def __init__(self, app, pref_title, pref_name, button_map, dial_map):
        super().__init__(app)
        self.pref_title = pref_title
        self.pref_name = pref_name

        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)

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
                Press.LONG: 'BACK',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)

        self.menu = ASCII_TEXT_ENTRY_MENU
        self.menu_index = 0
        self.menu_selected = False
        self.char_indexes = [0] * len(self.menu)

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()

        label = self.frame.new_label(self.pref_title, FONT)
        self.frame.paste(1, 0, label, cv=self.cv)
        self.text = self.app.prefs.get(self.pref_name)
        self.draw()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def draw(self):
        self.frame.clear()
        label = self.frame.new_label(self.pref_title + ': ', FONT)
        self.frame.paste(0, 0, label, cv=self.cv)
        text_label = self.frame.new_label(self.text, FONT)
        self.frame.paste(label.w, 0, text_label, cv=self.cursor_cv)
        self.frame.fill(label.w + text_label.w, 9, 5, 1, cv=self.cursor_cv)
        x = 5
        for i, option in enumerate(self.menu):
            title, command, chars = option
            label = self.frame.new_label(title, FONT)
            if i == self.menu_index:
                if self.menu_selected:
                    self.frame.paste(x, 10, label, cv=self.cursor_cv)

                    chars_label = self.frame.new_label(chars, FONT)
                    self.frame.paste(5, 21, chars_label, cv=self.cv)

                    ci = self.char_indexes[self.menu_index]
                    left = self.frame.new_label(chars[:ci], FONT).w
                    w = self.frame.new_label(chars[ci], FONT).w
                    self.frame.fill(5 + left, 31, w - 1, 1, cv=self.cursor_cv)
                else:
                    self.frame.paste(x, 10, label, cv=self.cv)
                    self.frame.fill(x, 20, label.w - 1, 1, cv=self.cursor_cv)
            else:
                self.frame.paste(x, 10, label, cv=self.cv)
            x += label.w + 4
        self.frame.send()

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

        if command == 'PROCEED':
            title, command, chars = self.menu[self.menu_index]
            if self.menu_selected:
                ci = self.char_indexes[self.menu_index]
                if ci == 0:
                    self.menu_selected = False
                else:
                    self.text += chars[ci]
            elif not command:
                self.menu_selected = True
            # Fall through to handle the new value of command

        if command == 'BACK':
            self.menu_selected = False
        if command == 'BACKSPACE':
            print('%r' % self.text)
            self.text = self.text[:-1]
            print('-> %r' % self.text)
        if command == 'CLEAR':
            self.text = ''

        if command == 'ACCEPT':
            self.app.prefs.set(self.pref_name, self.text)
            self.app.receive('MENU_MODE')
        else:
            self.draw()

    def move_menu_cursor(self, delta):
        self.menu_index = max(0, min(len(self.menu) - 1, self.menu_index + delta))

    def move_char_cursor(self, delta):
        title, command, chars = self.menu[self.menu_index]
        ci = self.char_indexes[self.menu_index]
        self.char_indexes[self.menu_index] = max(0, min(len(chars) - 1, ci + delta))
