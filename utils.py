import fs
import gc
import micropython
import os
import sys

debug = False


def free():
    return 0


if hasattr(gc, 'mem_free'):
    def free():
        gc.collect()
        return gc.mem_free()


def version_running():
    return sys.path[0]


def versions_present():
    versions = []
    for name in fs.listdir():
        if name.startswith('v') and fs.isdir(name):
            pack_name = name.split('.')[0]
            enabled_star = '*' if fs.isfile(name + '/@ENABLED') else ''
            versions.append(enabled_star + pack_name)
    return versions


last_ms = None
last_mem = None

def log(message=None, dump=False):
    global last_ms
    global last_mem
    import time
    ms = time.monotonic_ns()//1000000
    mem = free()
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
    proto, rest = url.split(':', 1)
    if proto == 'http' or proto == 'https':
        hostname, path = rest.lstrip('/').split('/', 1)
        return proto == 'https', hostname, '/' + path
    return None, None, None


class Cycle:
    def __init__(self, *items):
        self.items = items
        self.index = 0

    def get(self, delta=0):
        self.index = (self.index + len(self.items) + delta) % len(self.items)
        return self.items[self.index]
