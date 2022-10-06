import os
import sys
import time
import traceback

# The current directory should never be changed from '/'.
#
# Directories containing software versions have names of the form:
#     v<N>.<hash>, e.g. v2.68b329da9893e34099c7d8ad5cb9c940
#         for a complete directory (all files in version N)
#     v<N>-<M>.<hash>, e.g. v4-1.401b30e3b8b5d629635a5c613cdb7919
#         for a patch directory (just files that differ from version M to N)
#
# In all distributions, a complete v0 directory will be present, and a
# a factory reset will remove all other versions, leaving only v0.


def get_latest_usable_version():
    # The status of each software version directory is marked by the presence
    # or absence of two empty files that are not part of the downloaded pack:
    #
    #     @ENABLED: The version directory is enabled.
    #     @VALID: The version directory is completely downloaded and verified.
    #
    # Patch directories also contain a "@PATH" file, a whitespace-separated
    # list of the entries that should be added to sys.path.  The "@PATH" file
    # is an extension point; it can be included in the distributed software
    # pack for simplicity, or computed by other logic that we add later.
    #
    # We will run the latest version that is @ENABLED and for which every
    # directory in its @PATH is @VALID.
    latest_version = (-1, '', [])
    count = 0
    for name in os.listdir():
        try:
            assert name.startswith('v')
            pack_name = name.split('.')[0]
            number = int(pack_name[1:].split('-')[0])
        except:
            continue
        try:
            os.stat(name + '/@ENABLED')
            path = [name]
            try:
                path += open(name + '/@PATH').readline().split()
            except:
                pass
            for dir in path:
                os.stat(dir + '/@VALID')
        except:
            continue
        version = (number, name, path)
        if version > latest_version:
            # It just so happens that '-' sorts before '.', so when there are
            # multiple versions with the same number, we will prefer a complete
            # directory (when available) over a patch directory.
            latest_version = version
        count += 1
    return latest_version, count


(number, name, path), count = get_latest_usable_version()
if name:
    print(f'\nRunning version {number} with path {path}.\n')
    try:
        import sim
        sim.init(path)
    except:
        sys.path[:] = path  # sys.path cannot be assigned in CircuitPython
    start_time = int(time.monotonic())
    try:
        import start
    except Exception as e:
        run_time = int(time.monotonic()) - start_time

        # Downgrade to the previous usable version.
        if count > 1:
            print(f'\nDisabling /{name} due to crash: {e}\n')
            try:
                os.remove(name + '/@ENABLED')
            except Exception as ee:
                print(f'Could not disable /{name}: {ee}')
        else:
            print(f'\n/{name} is the last usable version; not disabling.\n')

        # Print and log the exception.
        try:
            traceback.print_exception(e, e, e.__traceback__)
            try:
                import cctime
                timestamp = cctime.get_millis()//1000
            except:
                timestamp = int(time.time())
            filename = f'{timestamp}-{run_time}.exc'
            with open(filename, 'w') as f:
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
            import microcontroller
            microcontroller.reset()
else:
    print('\nNo usable versions found.\n')
