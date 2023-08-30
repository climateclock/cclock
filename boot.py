import board
import digitalio
import microcontroller
import neopixel
import os
import storage
import supervisor
import time


def check_for_factory_reset():
    start = time.monotonic_ns()//1000000
    elapsed = 0

    # Button values are normally high (True) and go low (False) when pressed.
    while (not up.value) or (not down.value) or (not enter.value):
        elapsed = time.monotonic_ns()//1000000 - start
        if elapsed < 5000:
            # Pulse to show that the factory reset command is detected.
            pixel.fill(((elapsed / 4) % 250, 0, 0))
        elif elapsed < 10000:
            # Go solid to show that the factory reset command is confirmed.
            pixel.fill((255, 0, 192))  # [F]uchsia means [F]actory reset
        else:
            # Go dark to show that a factory reset will not be performed.
            pixel.fill((0, 0, 0))

    # The button has to be held for a long time (5 s) so that it's hard to
    # cause a factory reset accidentally, but not too long (10 s) so that it's
    # possible to cancel if you didn't want a factory reset, and a factory
    # reset is unlikely to be triggered by a short or other electrical problem.
    if 5000 < elapsed < 10000:
        factory_reset()
    if elapsed >= 5000:
        time.sleep(1)  # allow time to release buttons and see reset status
        global dev
        dev = False


def factory_reset():
    pixel.fill((255, 255, 0))
    storage.remount('/', readonly=False)

    def destroy(path):
        if os.stat(path)[0] & 0x4000:
            for name in os.listdir(path):
                destroy(path + '/' + name)
            os.rmdir(path)
        else:
            os.remove(path)

    errors = 0
    for name in os.listdir():
        if os.stat(name)[0] & 0x4000 and not name.startswith('v5.'):
            try:
                destroy(name)
            except Exception as e:
                errors += 1
                print(f'Removing {name}: {e}')

    pixel.fill((0, 255, 0) if errors == 0 else (255, 0, 0))


def set_development_mode(dev):
    if dev:
        pixel.fill((48, 0, 0))  # [R]ed means you can w[R]ite
    else:
        # Otherwise, the filesystem is writable from Python so that the
        # software can update itself.
        pixel.fill((0, 0, 64))  # [B]lue means [B]roduction mode
        storage.remount('/', readonly=False)
        supervisor.runtime.autoreload = False

up = digitalio.DigitalInOut(board.BUTTON_UP)
up.pull = digitalio.Pull.UP
down = digitalio.DigitalInOut(board.BUTTON_DOWN)
down.pull = digitalio.Pull.UP
enter = digitalio.DigitalInOut(board.TX)
enter.pull = digitalio.Pull.UP
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
dev = (not up.value) or (not down.value) or (not enter.value)
check_for_factory_reset()
set_development_mode(dev)
up.deinit()
down.deinit()
enter.deinit()
