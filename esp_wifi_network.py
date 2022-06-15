from adafruit_esp32spi import adafruit_esp32spi
import board
import busio
import cctime
import gpio
from network import Network, State


def to_bytes(bytes_or_string):
    if isinstance(bytes_or_string, bytes):
        return bytes_or_string
    return bytes(str(bytes_or_string), 'ascii')


class EspWifi(adafruit_esp32spi.ESP_SPIcontrol):
    """Patched version of ESP_SPIcontrol that resets without sleeping."""
    reset_started_ms = 0

    def reset(self):
        if self._debug:
            print('Resetting ESP32.')
        if self._gpio0:
            self._gpio0.direction = Direction.OUTPUT
            self._gpio0.value = True  # not bootload mode
        self._cs.value = True
        self._reset.value = False
        cctime.sleep(0.01)  # reset
        self._reset.value = True
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT
        self.reset_started = cctime.monotonic()

    def is_ready(self):
        if self.reset_started_ms:
            if cctime.monotonic() < self.reset_started_ms + 0.75:
                return False
            self.reset_started_ms = None
        return not self._ready.value

    def deinit(self):
        self._cs.deinit()
        self._ready.deinit()
        self._reset.deinit()


class EspWifiNetwork(Network):
    def __init__(self, debug=False):
        self.spi = None
        self.esp = None
        self.socket = None
        self.debug = debug
        self.wifi_retry_deadline_ms = None
        self.set_state(State.OFFLINE)

    def set_state(self, new_state):
        self.state = new_state
        if self.debug:
            print(f'Network is now {self.state}.')

    def enable_step(self, ssid, password):
        if not self.esp:
            esp32_cs = gpio.Output(board.ESP_CS)
            esp32_ready = gpio.Output(board.ESP_BUSY)
            esp32_reset = gpio.Output(board.ESP_RESET)
            self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            self.esp = EspWifi(self.spi, esp32_cs, esp32_ready, esp32_reset)
            self.esp._debug = self.debug
            self.esp.reset()

        elif self.esp.status == 3:
            self.set_state(State.ONLINE)

        elif self.esp.is_ready():
            if self.wifi_retry_deadline:
                if cctime.monotonic() > self.wifi_retry_deadline:
                    self.esp.reset()
                    self.wifi_retry_deadline_ms = None
                    return

            self.esp.wifi_set_passphrase(to_bytes(ssid), to_bytes(password))
            if not self.wifi_retry_deadline_ms:
                self.wifi_retry_deadline = cctime.monotonic() + 30

    def connect_step(self, hostname, port=None, ssl=True):
        if not self.socket:
            self.socket = self.esp.get_socket()
            mode = self.esp.TLS_MODE if ssl else self.esp.TCP_MODE
            port = port or (443 if ssl else 80)
            self.esp.socket_open(self.socket, hostname, port, mode)

        if self.esp.socket_connected(self.socket):
            self.set_state(State.CONNECTED)

    def send_step(self, data):
        if self.esp.socket_connected(self.socket):
            self.esp.socket_write(self.socket, data)
        else:
            self.set_state(State.ONLINE)

    def receive_step(self, count):
        if self.esp.socket_connected(self.socket):
            available = self.esp.socket_available(self.socket)
            if available:
                return self.esp.socket_read(self.socket, count)
            else:
                return b''
        else:
            self.set_state(State.ONLINE)

    def close_step(self):
        self.esp.socket_close(self.socket)
        self.set_state(State.ONLINE)

    def disable_step(self):
        if self.esp:
            self.esp.deinit()
            self.esp = None
        if self.spi:
            self.spi.deinit()
            self.spi = None
        self.set_state(State.OFFLINE)
