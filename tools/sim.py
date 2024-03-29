#!/usr/bin/env python3

import os
import sys

root = os.environ.get('CCLOCK_SIMULATOR_ROOT', '/tmp/cclock')
if not os.path.isdir(root):
    raise SystemExit(f"{root} not found; try doing 'tools/deploy -f -s' first.")

# All times on the board are in UTC.
os.environ['TZ'] = 'UTC'

# simulator_init.py installs the simulator monkey-patches.
os.environ['CCLOCK_SIMULATOR_PATH'] = os.getcwd() + '/simulator'
with open(root + '/simulator_init.py', 'w') as opt:
    with open('simulator/simulator_init.py') as ipt:
        opt.write(ipt.read())

# Off we go!
print('Simulator root:', root)
os.chdir(root)
sys.path = ['.'] + sys.path

import main
