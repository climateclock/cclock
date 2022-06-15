import adafruit_hashlib
from network import State


class PackLoader:
    PACK_FORMAT_VERSION = 1

    # For safety, we set an upper limit on the total size of the unpacked
    # files.  We aim to allow at least 4 versions to fit in flash storage.
    DISK_CAPACITY = 2*1024*1024  # total flash disk space available
    MAX_ROOT_SIZE = 512*1024  # max allotted for root files and lib/ directory
    MAX_UNPACKED_SIZE = (DISK_CAPACITY - MAX_ROOT_SIZE) / 4


    def __init__(self, network, hostname, path):
        if network.state != State.CONNECTED:
            raise ValueError('Network is not yet CONNECTED.')
        self.network = network
        self.buffer = bytearray()
        self.unpacked_size = 0
        self.block_type = b''
        self.block_length = 0
        self.pack_name = b'pack'
        self.pack_hash = b''
        self.file_path = b'file'

        self.network.send_step(
            b'GET ' + path + b' HTTP/1.1\r\n' +
            b'Host: ' + hostname + b'\r\n' +
            b'Connection: Close\r\n' +
            b'\r\n'
        )
        self.next_step = self.read_magic_step
        self.md5 = adafruit_hashlib.md5()

    def extend_buffer(self, target_length=1024):
        if len(self.buffer) < target_length:
            count = max(1024, target_length - len(self.buffer))
            self.buffer.extend(self.network.receive_step(count))
        return len(self.buffer) >= target_length

    def read_magic_step(self):
        if not self.extend_buffer(4):
            return
        if self.buffer[:2] != b'pk':
            raise ValueError(f'Invalid magic {self.buffer[:2]}')
        version = (self.buffer[2] << 8) + self.buffer[3]
        if version > self.PACK_FORMAT_VERSION:
            raise ValueError(f'Unsupported version {version}')
        print(f'Unpacking version {version}')
        self.buffer[:4] = b''
        self.next_step = self.read_block_header_step

    def read_block_header_step(self):
        if not self.extend_buffer(4):
            return
        self.block_type = self.buffer[2:]
        self.block_length = (self.buffer[2] << 8) + self.buffer[3]
        self.buffer[:4] = b''
        self.next_step = self.read_block_content_step

    def read_block_content_step(self):
        if not self.extend_buffer(self.block_length):
            return
        content = self.buffer[:self.block_size][:]
        self.buffer[:self.block_size] = b''
        done = self.handle_block(self.block_type, content)
        if done:
            self.next_step = lambda: True
            return True
        self.next_step = self.read_block_header_step

    def handle_block(self, block_type, content):
        print(f'Unpacking {block_type} block: {repr(content)}')

        if block_type == b'pn':  # pack name
            self.pack_name = content.replace(b'/', '')
        if block_type == b'ph':  # pack hash
            self.pack_hash = content
            self.dir_name = self.pack_name + b'.' + self.pack_hash
        if block_type == b'fn':  # file name
            md5.update(content)
            self.file_path = self.dir_name + b'/' + content
        if block_type == b'fc':  # file chunk
            self.unpacked_size += len(content)
            if self.unpacked_size > self.MAX_UNPACKED_SIZE:
                raise ValueError(
                    f'Pack exceeded limit of {self.MAX_UNPACKED_SIZE} bytes.')
            md5.update(content)
            append_to_file(self.file_path, content)
        if block_type == b'pe':  # pack end
            actual_hash = md5.hexdigest()
            if actual_hash == self.pack_hash:
                append_to_file(self.dir_name + b'/@VALID', b'')
                return True
            raise ValueError(
                f'Bad MD5 hash {actual_hash}; expected {self.pack_hash}')


def append_to_file(path, content):
    os.chdir(b'/')
    parts = path.split(b'/')
    for part in parts[:-1]:
        if not exists(part):
            os.mkdir(part)
        os.chdir(part)
    with open(parts[-1], 'a') as file:
        file.write(content)


def exists(name):
    try:
        os.stat(name)
        return True
    except:
        return False
