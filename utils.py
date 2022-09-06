import gc
import time


def free():
    return 0


if hasattr(gc, 'mem_free'):
    def free():
        gc.collect()
        return gc.mem_free()


last_ms = None
last_mem = None

def log(message=None):
    global last_ms
    global last_mem
    ms = time.monotonic_ns()//1000000
    mem = free()
    if message:
        sms = str(ms)
        msg = f'[{sms[:-3]}.{sms[-3:]}: {mem} free] {message}'
        if last_ms:
            dms = str(ms - last_ms)
            if len(dms) < 4:
                dms = ('0000' + dms)[-4:]
            dmem = last_mem - mem
            print(msg, f'[{dms[:-3]}.{dms[-3:]} s elapsed, {dmem} used]')
            last_ms = None
            last_mem = None
        else:
            print(msg)
    else:
        last_ms = ms
        last_mem = mem


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

    def current(self):
        return self.items[self.index]

    def next(self):
        self.index = (self.index + 1) % len(self.items)
        return self.items[self.index]

    def previous(self):
        self.index = (self.index + len(self.items) - 1) % len(self.items)
        return self.items[self.index]
