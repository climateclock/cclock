import os
import sys


def init(path):
    sys.path = path + [os.environ['CCLOCK_SIMULATOR_PATH']] + sys.path

    # Install monkey-patches.
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
