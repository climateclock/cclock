def to_bytes(arg):
    if isinstance(arg, bytes):
        return arg
    return bytes(str(arg), 'ascii')


def to_str(arg):
    if isinstance(arg, bytes):
        return str(arg, 'ascii')
    return str(arg)
