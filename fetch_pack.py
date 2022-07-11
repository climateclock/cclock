import board
import busio
from digitalio import DigitalInOut
import adafruit_requests as requests
from adafruit_esp32spi import adafruit_esp32spi
import time
import supervisor
import os

class EspWifi(adafruit_esp32spi.ESP_SPIcontrol):
    reset_waiting_until = 0

    """Patched version of ESP_SPIcontrol that resets without sleeping."""
    def reset(self):
        if self._debug:
            print("Reset ESP32")
        if self._gpio0:
            self._gpio0.direction = Direction.OUTPUT
            self._gpio0.value = True  # not bootload mode
        self._cs.value = True
        self._reset.value = False
        time.sleep(0.01)  # reset
        self._reset.value = True
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT
        self.reset_waiting_until = supervisor.ticks_ms() + 750

    def is_ready(self):
        if self.reset_waiting_until:
            if supervisor.ticks_ms() < self.reset_waiting_until:
                return False
        return not self._ready.value

    def deinit(self):
        self._cs.deinit()
        self._ready.deinit()
        self._reset.deinit()


class PackFetcher:
    def __init__(self, hostname, path):
        self.next_step = self.setup_esp
        self.hostname = hostname
        self.path = path
        self.pack_name = b'pack'
        self.pack_hash = b'0'
        self.dir_name = b'pack.0'
        self.block_type = b''
        self.block_size = 0
        self.s = 0

    def next(self):
        if not self.next_step:
            print('/', end='')
            return
        start = supervisor.ticks_ms()
        print(self.next_step.__name__, end=': ')
        try:
            self.next_step()
        except Exception as e:
            print(f'aborting request: {e}')
            self.deinit()
            self.next_step = None
        finish = supervisor.ticks_ms()
        print(finish - start, 'ms')

    def setup_esp(self):
        esp32_cs = DigitalInOut(board.ESP_CS)
        esp32_ready = DigitalInOut(board.ESP_BUSY)
        esp32_reset = DigitalInOut(board.ESP_RESET)
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        self.esp = EspWifi(self.spi, esp32_cs, esp32_ready, esp32_reset)
        self.next_step = self.wait_for_esp

    def wait_for_esp(self):
        if self.esp.is_ready:
            self.next_step = self.start_wifi

    def start_wifi(self):
        self.esp.wifi_set_passphrase(b'climateclock', b'climateclock')
        self.next_step = self.wait_for_wifi

    def wait_for_wifi(self):
        if self.esp.status == 3:
            self.next_step = self.open_socket

    def open_socket(self):
        self.s = self.esp.get_socket()
        self.esp.socket_open(self.s, self.hostname, 443, self.esp.TLS_MODE)
        self.next_step = self.wait_for_socket

    def wait_for_socket(self):
        if self.esp.socket_connected(self.s):
            self.esp.socket_write(self.s, f'GET {self.path} HTTP/1.1\r\n')
            self.esp.socket_write(self.s, f'Host: {self.hostname}\r\n')
            self.esp.socket_write(self.s, 'Connection: Close\r\n')
            self.esp.socket_write(self.s, '\r\n')
            self.buffer = bytearray()
            self.next_step = self.read_http

    def extend_buffer(self, target_size=1024):
        if len(self.buffer) >= target_size:
            return True
        if not self.esp.socket_connected(self.s):
            raise RuntimeError('disconnected')
        avail = self.esp.socket_available(self.s)
        if avail:
            count = max(1024, target_size - len(self.buffer))
            self.buffer.extend(self.esp.socket_read(self.s, count))
            print('extend', target_size, self.buffer)
        return len(self.buffer) >= target_size

    def read_http(self):
        i = self.buffer.find(b'\r\n\r\n')
        if i < 0:
            self.extend_buffer()
            return

        print('found HTTP content')
        self.buffer[:i + 4] = b''
        print(self.buffer)
        self.next_step = self.read_magic

    def read_magic(self):
        if not self.extend_buffer(4):
            return

        if self.buffer[:2] != b'pk':
            raise ValueError(f'invalid magic {self.buffer}')
        version = (self.buffer[2] << 8) + self.buffer[3]
        if version > 1:
            raise ValueError(f'unsupported version {version}')
        print(f'Unpacking version {version}')
        self.buffer[:4] = b''
        self.next_step = self.read_header

    def read_header(self):
        if not self.extend_buffer(4):
            return

        self.block_type = self.buffer[:2]
        self.block_size = (self.buffer[2] << 8) + self.buffer[3]
        self.buffer[:4] = b''
        self.next_step = self.read_block

    def read_block(self):
        if not self.extend_buffer(self.block_size):
            return

        self.handle_block(self.block_type, self.buffer[:self.block_size][:])
        self.buffer[:self.block_size] = b''
        self.next_step = self.read_header

    def handle_block(self, block_type, block):
        print(f'block {block_type} {block}')
        if block_type == b'fc':
            if len(block) != 2:
                raise ValueError(f'fc block has length {len(block)}')
            self.file_count = (block[0] << 8) + block[1]

        if block_type == b'pn':
            self.pack_name = block

        if block_type == b'ph':
            self.pack_hash = block
            self.dir_name = b'/' + self.pack_name + b'.' + self.pack_hash

        if block_type == b'fn':
            self.file_name = block

        if block_type == b'fb':
            self.write_file(self.file_name, block)

        if block_type == b'\x00\x00':
            self.next_step = self.verify

    def write_file(self, path, block):
        os.chdir(self.dir_name)
        parts = bytes(path).split(b'/')
        name = parts.pop()
        for part in parts:
            if not exists(part):
                print(f'mkdir {part}')
                os.mkdir(part)
            print(f'chdir {part}')
            os.chdir(part)
        print(f'write to {parts[-1]}')
        with open(name, 'a') as file:
            file.write(block)
        os.chdir(b'/')

    def verify(self):
        os.chdir(self.dir_name)
        # TODO: Check the content hash
        open('@VALID', 'w').close()

    def deinit(self):
        self.esp.socket_close(self.s)
        self.esp.deinit()
        self.spi.deinit()
        self.next_step = None

def exists(name):
    try:
        os.stat(name)
        return True
    except:
        return False

def run(*args):
    req = PackFetcher('example.com', '/cclock.pk')
    for i in range(50):
        req.next()
        time.sleep(0.5)
    req.deinit()
