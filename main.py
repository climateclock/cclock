import os
import supervisor
import sys

# Directories containing software versions are named v1, v2, etc.  We need
# a way to mark software versions as enabled, disabled, or partial, and we
# can't atomically move directories (os.rename doesn't work on directories
# in CircuitPython), so we mark each directory by creating empty files to
# indicate its status.  There can be two such files:
#
#     @ENABLED: The software version is enabled.
#     @VALID: The software version is completely downloaded and verified.

# The current directory should never be changed from '/'.
os.chdir('/')

versions = []
for name in os.listdir():
    try:
        assert name.startswith('v')
        pack_name = name.split('.')[0]
        num = int(pack_name[1:])
    except:
        continue
    try:
        os.stat(name + '/@VALID')
        os.stat(name + '/@ENABLED')
    except OSError:
        continue
    versions.append((num, name))

if versions:
    latest, name = max(versions)
    print(f'\nRunning /{name} (version {latest}).\n')
    sys.path[:0] = [name]
    try:
        import start
    except Exception as e:
        if len(versions) > 1:
            print(f'\nDisabling /{name} due to crash: {e}\n')
            try:
                os.remove(name + '/@ENABLED')
            except Exception as ee:
                print(f'{repr(ee)}: {ee}')
        else:
            print(f'\n/{name} is the last available version; not disabling.\n')
        raise
else:
    print('\nNo valid, enabled versions found.\n')
