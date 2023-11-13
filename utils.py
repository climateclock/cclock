import gc
import microcontroller
import micropython
import re
import storage
import sys

debug = False


def shut_down(power_sensor):
    log(f'Power at {power_sensor.level}%; shutting down')
    storage.umount('/')
    log(f'Storage has been unmounted')
    while power_sensor.level < 5:
        pass
    log(f'Power has returned after shutdown; resetting')
    microcontroller.reset()


def free():
    return 0


if hasattr(gc, 'mem_free'):
    def free():
        gc.collect()
        return gc.mem_free()


def version_num():
    return int(sys.path[0][1:].split('.')[0].split('-')[0])


def version_dir():
    return sys.path[0]


def versions_present():
    import fs  # ignored by sort_imports
    versions = []
    for name in fs.listdir():
        if name.startswith('v') and fs.isdir(name):
            if fs.isfile(name + '/@VALID'):
                pack_name = name.split('.')[0]
                enabled_flag = '*' if fs.isfile(name + '/@ENABLED') else ''
                versions.append(enabled_flag + pack_name)
    return versions


last_ms = None
last_mem = None
min_mem = free()


def log(message=None, dump=False):
    global last_ms
    global last_mem
    global min_mem
    import time
    ms = time.monotonic_ns()//1000000
    mem = free()
    min_mem = min(min_mem, mem)
    if message:
        msg = f'[{format_ms(ms)}: {mem} free] {message}'
        if last_ms:
            print(msg, f'[{format_ms(ms - last_ms)} s elapsed, {last_mem - mem} used]')
            last_ms = None
            last_mem = None
        else:
            print(msg)
    else:
        last_ms = ms
        last_mem = mem
    if dump or debug:
        gc.collect()
        micropython.mem_info(1)
        print()


def format_ms(ms):
    digits = str(ms)
    if len(digits) < 4:
        digits = ('0000' + digits)[-4:]
    return digits[:-3] + '.' + digits[-3:]


def to_bytes(arg):
    if isinstance(arg, bytes):
        return arg
    return bytes(str(arg), 'ascii')


def to_str(arg):
    if isinstance(arg, bytes):
        return str(arg, 'ascii')
    return str(arg)


def report_error(e, message):
    try:
        import traceback
        print(f'{message} due to:')
        traceback.print_exception(e, e, e.__traceback__)
    except:
        print(f'{message}: {e} {repr(e)}')


def split_url(url):
    match = re.match(r'^http(s?):/+([^/]+)(.*)', url)
    if match:
        return bool(match.group(1)), match.group(2), match.group(3) or '/'
    return None, None, None


class Cycle:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def get(self, delta=0, index=None):
        new_index = self.index + delta if index is None else index
        self.index = (new_index + len(self.items)) % len(self.items)
        return self.items[self.index]


class NullContext:
    def __enter__(*args): pass
    def __exit__(*args): pass

null_context = NullContext()
