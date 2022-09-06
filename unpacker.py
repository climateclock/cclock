import fs
from md5 import md5
from utils import to_str


MAX_PACK_FORMAT_VERSION = 1

# To limit memory use, we extend the unpacking buffer this much at a time.
MAX_CHUNK_LENGTH = 1024

# For safety, we set an upper limit on the total size of the unpacked
# files.  We aim to allow at least 4 versions to fit in flash storage.
DISK_CAPACITY = 2*1024*1024  # total flash disk space available
MAX_ROOT_SIZE = 512*1024  # max allotted for root files and lib/ directory
MAX_UNPACKED_SIZE = (DISK_CAPACITY - MAX_ROOT_SIZE) / 4

class Unpacker:
    def __init__(self, stream):
        self.stream = stream

        self.buffer = bytearray()
        self.unpacked_size = 0
        self.block_type = b''
        self.block_length = 0
        self.pack_name = b''
        self.pack_hash = b''
        self.dir_name = b''
        self.file_path = b''
        self.digest = md5()
        self.step = self.magic_step

    def extend_buffer(self, target_length):
        if len(self.buffer) < target_length:
            count = max(MAX_CHUNK_LENGTH, target_length - len(self.buffer))
            self.buffer.extend(self.stream.read())
        return len(self.buffer) >= target_length

    def magic_step(self):
        """Reads and verifies the first 4 bytes of the pack file."""
        if not self.extend_buffer(4):
            return
        magic = self.buffer[:2]
        if magic != b'pk':
            raise ValueError(f'Invalid magic {bytes(magic)}')
        version = (self.buffer[2] << 8) + self.buffer[3]
        if version > MAX_PACK_FORMAT_VERSION:
            raise ValueError(f'Unsupported version {version}')
        print(f'Receiving pack version {version}')
        self.buffer[:4] = b''
        self.step = self.block_header_step
        return self.step()

    def block_header_step(self):
        """Reads the 4-byte header of a block."""
        if not self.extend_buffer(4):
            return
        self.block_type = self.buffer[:2]
        self.block_length = (self.buffer[2] << 8) + self.buffer[3]
        self.buffer[:4] = b''
        self.step = self.block_content_step
        return self.step()

    def block_content_step(self):
        """Reads a block, splitting long blocks into chunks. """
        chunk_length = min(MAX_CHUNK_LENGTH, self.block_length)
        if not self.extend_buffer(chunk_length):
            return
        content = self.buffer[:chunk_length]
        self.buffer[:chunk_length] = b''
        done = self.handle_block(self.block_type, content)
        if done:
            return True
        self.block_length -= chunk_length
        if self.block_length == 0:
            self.step = self.block_header_step
            return self.step()

    def handle_block(self, block_type, content):
        """Handles a block according to its type."""
        content = bytes(content)
        print(
            f'Received {bytes(block_type)} block ' +
            f'{len(content) < 20 and content or "(%d bytes)" % len(content)}')

        if block_type == b'pn':  # pack name
            self.pack_name = to_str(content).replace('/', '')

        if block_type == b'ph':  # pack hash
            self.pack_hash = to_str(content)
            self.dir_name = self.pack_name + '.' + self.pack_hash
            if fs.isdir(self.dir_name):
                if fs.isfile(self.dir_name + '/@VALID'):
                    print(f'{self.dir_name} already exists and is valid.')
                    return True
                else:
                    print(f'Removing incomplete {self.dir_name}.')
                    fs.destroy(self.dir_name)

        if block_type == b'fn':  # file name
            self.file_path = self.dir_name + '/' + to_str(content)
            self.digest.update(content)

        if block_type == b'fc':  # file chunk
            self.unpacked_size += len(content)
            if self.unpacked_size > MAX_UNPACKED_SIZE:
                raise ValueError(
                    f'Pack exceeded limit of {MAX_UNPACKED_SIZE} bytes.')
            self.digest.update(content)
            fs.write(self.file_path, content, 'ab')

        if block_type == b'pe':  # pack end
            actual_hash = self.digest.hexdigest()
            if actual_hash == self.pack_hash:
                fs.write(self.dir_name + '/@VALID', b'')
                print(f'Pack {self.dir_name} unpacked successfully!')
                return True
            raise ValueError(
                f'Bad MD5 hash {actual_hash}; expected {self.pack_hash}')

