import os
import sys

original_path = sys.path[:]


def install_monkey_patches():
    # Install monkey-patches.
    sys.path.append(os.environ['CCLOCK_SIMULATOR'])
    sys.path += original_path

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


def reset():
    print('\nmicrocontroller.reset() called; exiting simulator.')
    sys.exit(1)
