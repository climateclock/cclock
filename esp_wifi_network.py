from adafruit_esp32spi import adafruit_esp32spi
import board
import busio
import cctime
from digitalio import DigitalInOut, Direction
from network import Network, State
import utils
from utils import to_bytes


class EspWifi(adafruit_esp32spi.ESP_SPIcontrol):
    """Patched version of ESP_SPIcontrol that resets without sleeping."""
    reset_started = None

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
        if self.reset_started:
            if cctime.monotonic() < self.reset_started + 0.75:
                return False
            self.reset_started = None
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
        self.wifi_started = None
        self.socket_started = None
        self.set_state(State.OFFLINE)

    def get_firmware_version(self):
        if self.esp:
            return str(bytes(self.esp.firmware_version), 'ascii')
        return 'None'

    def get_hardware_address(self):
        if self.esp:
            return ':'.join('%02x' % byte for byte in self.esp.MAC_address)
        return 'None'

    def set_state(self, new_state):
        self.state = new_state
        print(f'Network is now {self.state}.')

    def enable_step(self, ssid, password):
        if not self.esp:
            print('Initializing ESP32.')
            esp32_cs = DigitalInOut(board.ESP_CS)
            esp32_ready = DigitalInOut(board.ESP_BUSY)
            esp32_reset = DigitalInOut(board.ESP_RESET)
            self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
            self.esp = EspWifi(self.spi, esp32_cs, esp32_ready, esp32_reset)
            self.esp._debug = self.debug

        elif not self.wifi_started:
            if self.esp.is_ready():
                print(f'Joining Wi-Fi network {repr(ssid)}.')
                # NOTE: ssid and password must be bytes, not str!
                self.esp.wifi_set_passphrase(to_bytes(ssid), to_bytes(password))
                self.wifi_started = cctime.monotonic()

        elif self.wifi_started:
            # NOTE: Reading esp.status is only safe in certain states; it
            # cause a crash if wifi_set_passphrase hasn't been called yet.
            esp_status = self.esp.status

            if esp_status == 3:
                self.set_state(State.ONLINE)

            elif esp_status == 4:
                print(f'Failed to join Wi-Fi network {repr(ssid)}.')
                self.wifi_started = None

            elif cctime.monotonic() > self.wifi_started + 15:
                print('Could not join Wi-Fi network after 15 seconds; resetting.')
                self.esp.reset()
                self.wifi_started = None


    def connect_step(self, hostname, port=None, ssl=True):
        if self.socket is None:
            self.socket = self.esp.get_socket()
            port = port or (443 if ssl else 80)
            mode = self.esp.TLS_MODE if ssl else self.esp.TCP_MODE
            print(f'Connecting to', hostname, 'port', port)
            try:
                # NOTE: hostname must be str, not bytes!
                self.esp.socket_open(self.socket, hostname, port, mode)
                self.socket_started = cctime.monotonic()
            except Exception as e:
                utils.report_error(e, 'Failed to open socket')

        if self.esp.socket_connected(self.socket):
            print('Connected!')
            self.set_state(State.CONNECTED)

        else:
            if cctime.monotonic() > self.socket_started + 15:
                print('No connection after 15 seconds; retrying.')
                self.esp.socket_close(self.socket)
                self.socket = None

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
        if self.esp and self.socket:
            self.esp.socket_close(self.socket)
            self.set_state(State.ONLINE)
        self.socket = None

    def disable_step(self):
        self.close_step()
        if self.esp:
            self.esp.deinit()
            self.esp = None
        if self.spi:
            self.spi.deinit()
            self.spi = None
        self.set_state(State.OFFLINE)
