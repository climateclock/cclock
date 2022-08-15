import gc

def mem(*args):
    pass

if hasattr(gc, 'mem_free'):
    def mem(label):
        gc.collect()
        print(label, gc.mem_free())


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
        print(f'{message}: ', end='')
        traceback.print_exception(e, e, e.__traceback__)
    except:
        print(f'{message}: {e} {repr(e)}')


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
