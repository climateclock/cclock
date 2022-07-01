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

versions = []
for name in os.listdir('/'):
    try:
        assert name.startswith('v')
        base_name = name.split('.')[0]
        num = int(base_name[1:])
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
        import main
        main.main()
    except Exception as e:
        print('Error:', e)
        try:
            import traceback
            traceback.print_exception(e.__class__, e, e.__traceback__)
        except Exception as ee:
            print(repr(e))
        if len(versions) > 1:
            print(f'\nDisabling /{name} due to crash: {e}\n')
            try:
                os.remove(name + '/@ENABLED')
            except Exception as ee:
                print(ee)
        else:
            print(f'\nThis is the last available version; not disabling.\n')
        supervisor.reload()
else:
    print('\nNo valid, enabled versions found.\n')
