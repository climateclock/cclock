import os

# root is absolute and always starts with '/' unless it is empty
root = ''
open_file = open


def resolve(relpath):
    return root + '/' + relpath.strip('/')


def open(relpath, mode='rb'):
    make_parent(relpath)
    return open_file(resolve(relpath), mode)


def write(relpath, content, mode='wb'):
    make_parent(relpath)
    with open(relpath, mode) as file:
        file.write(content)


def move(relpath, newrelpath):
    destroy(newrelpath)
    os.rename(resolve(relpath), resolve(newrelpath))


def destroy(relpath):  # removes a file or directory and all descendants
    path = resolve(relpath)
    if isfile(relpath):
        os.remove(path)
    if isdir(relpath):
        for file in os.listdir(path):
            destroy(relpath + '/' + file)
        os.rmdir(path)


def isdir(relpath):
    return get_mode(relpath) & 0x4000


def isfile(relpath):
    return get_mode(relpath) & 0x8000


def get_mode(relpath):
    try:
        return os.stat(resolve(relpath))[0]
    except:
        return 0


def make_parent(relpath):
    parts = relpath.strip('/').split('/')
    relpath = ''
    for part in parts:
        path = resolve(relpath)
        if isfile(relpath):
            os.remove(path)
        if not isdir(relpath):
            os.mkdir(path)
        relpath += '/' + part
