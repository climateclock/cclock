import os

builtin_open = open


def open(path, mode='rb'):
    make_parent(path)
    return builtin_open(path, mode)


def move(path, newpath):
    destroy(newpath)
    os.rename(path, newpath)


def destroy(path):  # removes a file or directory and all descendants
    if isdir(path):
        for file in os.listdir(path):
            destroy(path + '/' + file)
        os.rmdir(path)
    if isfile(path):
        os.remove(path)


def free():
    _, frsize, _, _, bfree = os.statvfs('.')[:5]
    return frsize*bfree


def listdir():  # accept no arguments; only allow listing of /
    return os.listdir()


def isdir(path):
    return get_mode(path) & 0x4000


def isfile(path):
    return get_mode(path) & 0x8000


def get_mode(path):
    try:
        return os.stat(path)[0]
    except:
        return 0


def make_parent(path):
    parts = path.strip('/').split('/')
    path = parts[0]
    for part in parts[1:]:
        if isfile(path):
            os.remove(path)
        if not isdir(path):
            os.mkdir(path)
        path += '/' + part
