# This file is copied to /tmp/cclock and run from there; it puts simulator/
# on sys.path so the rest of the simulator modules can be imported.

import os
import sys


def init(path):
    sys.path[:0] = path + [os.environ['CCLOCK_SIMULATOR_PATH']]

    # In CircuitPython, traceback.format_exception returns a string.
    import traceback
    format_exception = traceback.format_exception
    traceback.format_exception = lambda *args: ''.join(format_exception(*args))

    # TODO: Remove fs, since we use the cwd now?
    import fs
    fs.root = '/tmp/cclock'

    import fake_cctime
    fake_cctime.install()

    import fake_display
    fake_display.install()

    import fake_inputs
    fake_inputs.install()

    import fake_network
    fake_network.install(b'climateclock', b'climateclock')
