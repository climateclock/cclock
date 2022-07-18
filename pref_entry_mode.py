from ccinput import ButtonReader, DialReader, Press
from mode import Mode


class PrefEntryMode(Mode):
    def __init__(self, app, pref_title, pref_name, button_map, dial_map):
        super().__init__(app)
        self.pref_title = pref_title
        self.pref_name = pref_name
        self.cv = self.frame.pack(0x80, 0x80, 0x80)
        self.cursor_cv = self.frame.pack(0x00, 0xff, 0x00)
        self.reader = ButtonReader({
            button_map['UP']: {
                Press.SHORT: 'NEXT_CHAR',
                Press.REPEAT: 'NEXT_CHAR',
            },
            button_map['DOWN']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'SAVE_PREF',
            },
            button_map['ENTER']: {
                Press.SHORT: 'ENTER_CHAR',
                Press.LONG: 'SAVE_PREF',
            }
        })
        self.dial_reader = DialReader('SELECTOR', dial_map['SELECTOR'], 1)
        self.charset = (
            ' aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ' +
            '0123456789' +
            '.,:;!?' +
            '\'"@#$%^&*+-_=*' +
            '/\\()[]<>{}~'
        )
        self.char_index = 0

    def start(self):
        self.reader.reset()
        self.dial_reader.reset()
        self.frame.clear()
        label = self.frame.new_label(self.pref_title, 'kairon-10')
        self.frame.paste(1, 0, label, cv=self.cv)
        self.text = ''
        self.draw_text()

    def step(self):
        self.reader.step(self.app.receive)
        self.dial_reader.step(self.app.receive)
        # TODO: Currently every mode's step() method must call self.frame.send()
        # in order for sdl_frame to detect events; fix this leaky abstraction.
        self.frame.send()

    def draw_char(self):
        self.char = self.charset[self.char_index]
        char_label = self.frame.new_label(self.char, 'kairon-10')
        x = 1 + self.text_label.w
        self.frame.paste(x, 16, char_label, cv=self.cursor_cv)
        self.frame.fill(x, 26, char_label.w - 1, 1, self.cv)
        self.frame.clear(x + char_label.w - 1, 16, 10, 12)

    def draw_text(self):
        self.text_label = self.frame.new_label(self.text, 'kairon-10')
        self.frame.paste(1, 16, self.text_label, cv=self.cv)
        self.frame.clear(1, 26, self.text_label.w, 1)
        self.draw_char()

    def receive(self, command, arg=None):
        if command == 'NEXT_CHAR':
            self.char_index = (self.char_index + 1) % len(self.charset)
            self.draw_char()
        if command == 'SELECTOR':
            delta, value = arg
            self.char_index = (self.char_index + len(self.charset) + delta) % len(self.charset)
            self.draw_char()
        if command == 'ENTER_CHAR':
            self.text += self.char
            self.draw_text()
        if command == 'SAVE_PREF':
            self.app.prefs.set(self.pref_name, self.text)
            self.app.receive('MENU_MODE')


