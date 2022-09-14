import microcontroller
import os
import sys
import time
import traceback

# Directories containing software versions are named v1.<hash>, v2.<hash>,
# etc.  We need a way to mark software versions as enabled, disabled, or
# partial, and we can't atomically move directories (os.rename doesn't work
# on directories in CircuitPython), so we mark each directory by creating
# empty files to indicate its status.  There can be two such files:
#
#     @ENABLED: The software version is enabled.
#     @VALID: The software version is completely downloaded and verified.

# The current directory should never be changed from '/'.
os.chdir('/')

def get_latest_enabled_version():
    versions = []
    for name in os.listdir():
        try:
            assert name.startswith('v')
            pack_name = name.split('.')[0]
            number = int(pack_name[1:])
        except:
            continue
        try:
            os.stat(name + '/@VALID')
            os.stat(name + '/@ENABLED')
        except OSError:
            continue
        versions.append((number, name))
    number = name = None
    if versions:
        number, name = max(versions)
    return number, name, len(versions)

number, name, count = get_latest_enabled_version()
if name:
    print(f'\nRunning /{name} (version {number}).\n')
    sys.path[:0] = [name]
    start_time = int(time.monotonic())
    try:
        import start
    except Exception as e:
        run_time = int(time.monotonic()) - start_time

        # Downgrade to the previous enabled version.
        if count > 1:
            print(f'\nDisabling /{name} due to crash: {e}\n')
            try:
                os.remove(name + '/@ENABLED')
            except Exception as ee:
                print(f'Could not disable /{name}: {ee}')
        else:
            print(f'\n/{name} is the last available version; not disabling.\n')

        # Print and log the exception.
        try:
            traceback.print_exception(e, e, e.__traceback__)
            try:
                import cctime
                timestamp = cctime.get_millis()//1000
            except:
                timestamp = int(time.time())
            with open(f'{timestamp}-{run_time}.exc', 'w') as f:
                f.write(traceback.format_exception(e, e, e.__traceback__))
            print(f'Wrote traceback to {filename}.')
        except Exception as ee:
            print(f'Could not write traceback: {ee}')

        # Restart.
        if run_time < 300:
            print(f'\nRunning time was only {run_time} s; not restarting.\n')
        else:
            print(f'\nRunning time was {run_time}s; restarting in 5 seconds.\n')
            time.sleep(5)
            microcontroller.reset()
else:
    print('\nNo valid, enabled versions found.\n')
