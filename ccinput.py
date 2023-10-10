"""Logic for detecting short, long, double, and autorepeated button presses."""

import cctime
import sys


class Press:
    SHORT = 'SHORT'
    LONG = 'LONG'
    DOUBLE = 'DOUBLE'
    REPEAT = 'REPEAT'
    RELEASE = 'RELEASE'

    # All durations are in milliseconds.
    DEBOUNCE_PERIOD = 10
    CHORD_PERIOD = 100
    MULTICLICK_INTERVAL = 150
    REPEAT_INTERVAL = 150
    LONG_PERIOD = 500


class ButtonReader:
    def __init__(self, buttons, command_map):
        self.buttons = buttons
        self.map = command_map
        self.reset()

    def reset(self):
        self.debounce_started = {key: None for key in self.map}
        self.was_pressed = {key: None for key in self.map}
        self.action_started = {key: None for key in self.map}
        self.last_clicked = {key: None for key in self.map}
        self.next_repeat = {key: None for key in self.map}
        self.waiting_for_release = True

    def step(self, receiver):
        if self.waiting_for_release:
            # .value goes low when button is pressed
            if any(self.buttons[key].value == False for key in self.map):
                return
            self.waiting_for_release = False

        if hasattr(sys.stdout, 'flush'):
            sys.stdout.flush()
        now = cctime.get_millis()
        for key, commands in self.map.items():
            if self.debounce_started[key]:
                if now < self.debounce_started[key] + Press.DEBOUNCE_PERIOD:
                    continue
                self.debounce_started[key] = None

            # .value goes low when button is pressed
            now_pressed = (self.buttons[key].value == False)
            if now_pressed != self.was_pressed[key]:
                self.debounce_started[key] = now

            just_pressed = now_pressed and not self.was_pressed[key]
            just_released = self.was_pressed[key] and not now_pressed
            action_ended = self.action_started[key] and just_released
            self.was_pressed[key] = now_pressed

            if just_pressed:
                self.action_started[key] = now
            if just_released:
                self.action_started[key] = None
            long_pressed = (
                self.action_started[key] and
                now > self.action_started[key] + Press.LONG_PERIOD
            )

            if just_pressed and list(commands.keys()) == [Press.SHORT]:
                receiver.receive(commands[Press.SHORT])
            elif Press.REPEAT in commands and self.next_repeat[key]:
                if just_released:
                    self.next_repeat[key] = None
                elif now > self.next_repeat[key]:
                    receiver.receive(commands[Press.REPEAT])
                    self.next_repeat[key] = now + Press.REPEAT_INTERVAL
            elif Press.REPEAT in commands and long_pressed:
                if Press.LONG in commands:
                    receiver.receive(commands[Press.LONG])
                receiver.receive(commands[Press.REPEAT])
                self.next_repeat[key] = now + Press.REPEAT_INTERVAL
            elif Press.DOUBLE in commands and action_ended:
                self.last_clicked[key] = now
            elif Press.DOUBLE in commands and self.last_clicked[key]:
                if now > self.last_clicked[key] + Press.MULTICLICK_INTERVAL:
                    self.last_clicked[key] = None
                    if Press.SHORT in commands:
                        receiver.receive(commands[Press.SHORT])
                elif just_pressed:
                    receiver.receive(commands[Press.DOUBLE])
                    self.action_started[key] = None
                    self.last_clicked[key] = None
            elif Press.LONG in commands and long_pressed:
                receiver.receive(commands[Press.LONG])
                self.action_started[key] = None
            elif Press.SHORT in commands and action_ended:
                receiver.receive(commands[Press.SHORT])
            if Press.RELEASE in commands and just_released:
                receiver.receive(commands[Press.RELEASE])

    def deinit(self):
        for io in self.ios:
            io.deinit()
        self.ios = {}


class DialReader:
    def __init__(self, command, dial, epsilon, min=None, max=None):
        self.command = command
        self.dial = dial
        self.epsilon = epsilon
        self.min = min
        self.max = max
        self.reset()

    def reset(self):
        self.last_position = self.dial.position

    @property
    def value(self):
        return self.dial.position

    def step(self, receiver):
        position = self.dial.position
        delta = position - self.last_position
        if (abs(delta) >= self.epsilon or
            position == self.min or position == self.max):
            self.last_position = position
            receiver.receive(self.command, (delta, position))

    def deinit(self):
        self.dial.deinit()
