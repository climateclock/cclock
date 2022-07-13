"""Logic for detecting short, long, double, and autorepeated button presses."""

import cctime
import sys


class Press:
    SHORT = 'SHORT'
    LONG = 'LONG'
    DOUBLE = 'DOUBLE'
    REPEAT = 'REPEAT'

    DEBOUNCE_PERIOD = 0.01
    CHORD_PERIOD = 0.1
    MULTICLICK_INTERVAL = 0.15
    REPEAT_INTERVAL = 0.15
    LONG_PERIOD = 0.5


class ButtonReader:
    def __init__(self, command_map):
        self.map = command_map
        self.immediate_buttons = set(
            button for button, commands in self.map.items()
            if Press.LONG not in commands
            if Press.DOUBLE not in commands
        )
        self.reset()

    def reset(self):
        self.debounce_started = {button: None for button in self.map}
        self.was_pressed = {button: None for button in self.map}
        self.action_started = {button: None for button in self.map}
        self.last_clicked = {button: None for button in self.map}
        self.next_repeat = {button: None for button in self.map}
        self.waiting_for_release = True

    def step(self, receiver):
        if self.waiting_for_release:
            if any(b.pressed for b in self.map):
                return
            self.waiting_for_release = False

        if hasattr(sys.stdout, 'flush'):
            sys.stdout.flush()
        now = cctime.monotonic()
        for button, commands in self.map.items():
            if self.debounce_started[button]:
                if now < self.debounce_started[button] + Press.DEBOUNCE_PERIOD:
                    continue
                self.debounce_started[button] = None

            now_pressed = button.pressed
            if now_pressed != self.was_pressed[button]:
                self.debounce_started[button] = now

            just_pressed = now_pressed and not self.was_pressed[button]
            released = self.was_pressed[button] and not now_pressed
            action_ended = self.action_started[button] and released
            self.was_pressed[button] = now_pressed

            if just_pressed:
                self.action_started[button] = now
            if released:
                self.action_started[button] = None
            long_pressed = (
                self.action_started[button] and
                now > self.action_started[button] + Press.LONG_PERIOD
            )

            if button in self.immediate_buttons:
                if Press.SHORT in commands and just_pressed:
                    receiver(commands[Press.SHORT])
                elif Press.REPEAT in commands and self.next_repeat[button]:
                    if released:
                        self.next_repeat[button] = None
                    elif now > self.next_repeat[button]:
                        receiver(commands[Press.REPEAT])
                        self.next_repeat[button] = now + Press.REPEAT_INTERVAL
                elif Press.REPEAT in commands and long_pressed:
                    receiver(commands[Press.REPEAT])
                    self.next_repeat[button] = now + Press.REPEAT_INTERVAL
            elif Press.DOUBLE in commands and action_ended:
                self.last_clicked[button] = now
            elif Press.DOUBLE in commands and self.last_clicked[button]:
                if now > self.last_clicked[button] + Press.MULTICLICK_INTERVAL:
                    self.last_clicked[button] = None
                    if Press.SHORT in commands:
                        receiver(commands[Press.SHORT])
                elif just_pressed:
                    receiver(commands[Press.DOUBLE])
            elif Press.LONG in commands and long_pressed:
                receiver(commands[Press.LONG])
                self.action_started[button] = None
            elif Press.SHORT in commands and action_ended:
                receiver(commands[Press.SHORT])

    def deinit(self):
        for io in self.ios:
            io.deinit()
        self.ios = {}


class DialReader:
    def __init__(self, command, dial, epsilon, min=None, max=None):
        self.command = command
        self.dial = dial
        self.last_value = dial.value
        self.epsilon = epsilon
        self.min = min
        self.max = max

    @property
    def value(self):
        return self.dial.value

    def step(self, receiver):
        value = self.dial.value
        delta = value - self.last_value
        if abs(delta) >= self.epsilon or value == self.min or value == self.max:
            self.last_value = value
            receiver(self.command, (delta, value))

    def deinit(self):
        self.dial.deinit()
