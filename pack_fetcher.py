try:
    from hashlib import md5
except:
    from adafruit_hashlib import md5
import os
from network import State


def to_bytes(arg):
    if isinstance(arg, bytes):
        return arg
    return bytes(str(arg), 'ascii')


class PackFetcher:
    MAX_PACK_FORMAT_VERSION = 1

    # For safety, we set an upper limit on the total size of the unpacked
    # files.  We aim to allow at least 4 versions to fit in flash storage.
    DISK_CAPACITY = 2*1024*1024  # total flash disk space available
    MAX_ROOT_SIZE = 512*1024  # max allotted for root files and lib/ directory
    MAX_UNPACKED_SIZE = (DISK_CAPACITY - MAX_ROOT_SIZE) / 4


    def __init__(self, fs, network, hostname, path):
        if network.state != State.CONNECTED:
            raise ValueError('Network is not yet CONNECTED.')
        self.fs = fs
        self.network = network
        self.buffer = bytearray()
        self.unpacked_size = 0
        self.block_type = b''
        self.block_length = 0
        self.pack_name = b'pack'
        self.pack_hash = b''
        self.file_path = b'file'

        self.network.send_step(
            b'GET ' + to_bytes(path) + b' HTTP/1.1\r\n' +
            b'Host: ' + to_bytes(hostname) + b'\r\n' +
            b'Connection: Close\r\n' +
            b'\r\n'
        )
        self.next_step = self.read_http_response_step
        self.digest = md5()

    def extend_buffer(self, target_length=256):
        """Reads bytes into the buffer until the buffer contains at least
        target_length bytes.  Returns True if the target length was reached."""
        if len(self.buffer) < target_length:
            count = max(256, target_length - len(self.buffer))
            self.buffer.extend(self.network.receive_step(count))
        return len(self.buffer) >= target_length

    def read_http_response_step(self):
        """Reads the HTTP status and skips all the HTTP headers."""
        if not self.extend_buffer(16):
            return
        if self.buffer[:5] != b'HTTP/' or b' ' not in self.buffer:
            raise ValueError(f'Invalid HTTP response {self.buffer}')
        words = bytes(self.buffer).split(b' ')
        if words[1] != b'200':
            raise ValueError(f'HTTP status {words[1]}')
        double_crlf = self.buffer.find(b'\r\n\r\n')
        if double_crlf < 0:
            self.extend_buffer(len(self.buffer) + 128)
            return
        self.buffer[:double_crlf + 4] = b''
        self.next_step = self.read_magic_step

    def read_magic_step(self):
        """Reads and verifies the first 4 bytes of the pack file."""
        if not self.extend_buffer(4):
            return
        magic = self.buffer[:2]
        if magic != b'pk':
            raise ValueError(f'Invalid magic {bytes(magic)}')
        version = (self.buffer[2] << 8) + self.buffer[3]
        if version > self.MAX_PACK_FORMAT_VERSION:
            raise ValueError(f'Unsupported version {version}')
        print(f'Receiving pack version {version}')
        self.buffer[:4] = b''
        self.next_step = self.read_block_header_step

    def read_block_header_step(self):
        """Reads the 4-byte header of a block."""
        if not self.extend_buffer(4):
            return
        self.block_type = self.buffer[:2]
        self.block_length = (self.buffer[2] << 8) + self.buffer[3]
        self.buffer[:4] = b''
        self.next_step = self.read_block_content_step

    def read_block_content_step(self):
        """Reads the contents of a block."""
        if not self.extend_buffer(self.block_length):
            return
        content = self.buffer[:self.block_length][:]
        self.buffer[:self.block_length] = b''
        done = self.handle_block(self.block_type, content)
        if done:
            raise StopIteration
        self.next_step = self.read_block_header_step

    def handle_block(self, block_type, content):
        """Handles a block according to its type."""
        content = bytes(content)
        print(
            f'Received {bytes(block_type)} block ' +
            f'{len(content) < 20 and content or "(%d bytes)" % len(content)}')

        if block_type == b'pn':  # pack name
            self.pack_name = content.replace(b'/', b'')
        if block_type == b'ph':  # pack hash
            self.pack_hash = content
            self.dir_name = self.pack_name + b'.' + self.pack_hash
            if self.fs.isdir(self.dir_name):
                if self.fs.isfile(self.dir_name + b'/@VALID'):
                    print(f'{self.dir_name} already exists and is valid.')
                    return True
                else:
                    print(f'Removing incomplete {self.dir_name}.')
                    self.fs.destroy(self.dir_name)
        if block_type == b'fn':  # file name
            self.file_path = self.dir_name + b'/' + content
            self.digest.update(content)
        if block_type == b'fc':  # file chunk
            self.unpacked_size += len(content)
            if self.unpacked_size > self.MAX_UNPACKED_SIZE:
                raise ValueError(
                    f'Pack exceeded limit of {self.MAX_UNPACKED_SIZE} bytes.')
            self.digest.update(content)
            self.fs.append(self.file_path, content)
        if block_type == b'pe':  # pack end
            actual_hash = bytes(self.digest.hexdigest(), encoding='ascii')
            if actual_hash == self.pack_hash:
                self.fs.write(self.dir_name + b'/@VALID', b'')
                return True
            raise ValueError(
                f'Bad MD5 hash {actual_hash}; expected {self.pack_hash}')
