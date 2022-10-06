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

    import sim_cctime
    sim_cctime.install()

    import sim_display
    sim_display.install()

    import sim_inputs
    sim_inputs.install()

    import sim_network
    sim_network.install(b'climateclock', b'climateclock')
