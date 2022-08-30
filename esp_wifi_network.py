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
        cctime.sleep_millis(10)  # reset
        self._reset.value = True
        if self._gpio0:
            self._gpio0.direction = Direction.INPUT
        self.reset_started = cctime.get_millis()

    def is_ready(self):
        if self.reset_started:
            if cctime.get_millis() < self.reset_started + 750:
                return False
            self.reset_started = None
        return not self._ready.value

    def deinit(self):
        self._cs.deinit()
        self._ready.deinit()
        self._reset.deinit()

    def safely_get_status(self):
        try:
            # NOTE: Reading esp.status is only safe in certain states.
            return self.status
        except Exception as e:
            utils.report_error(e, 'Could not get ESP32 status; resetting')
            self.reset()
            return None


class EspWifiNetwork(Network):
    def __init__(self, debug=False):
        self.spi = None
        self.esp = None
        self.debug = debug
        self.wifi_started = None
        self.socket = None
        self.socket_started = None
        self.set_state(State.OFFLINE)

    def get_firmware_version(self):
        if self.esp:
            return str(bytes(self.esp.firmware_version), 'ascii')
        return ''

    def get_hardware_address(self):
        if self.esp:
            return ':'.join('%02x' % byte for byte in self.esp.MAC_address)
        return ''

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
            self.wifi_started = None
            self.socket = None

        elif not self.wifi_started:
            if self.esp.is_ready():
                print(f'Joining Wi-Fi network {repr(ssid)}.')
                # NOTE: ssid and password must be bytes, not str!
                self.esp.wifi_set_passphrase(to_bytes(ssid), to_bytes(password))
                self.wifi_started = cctime.get_millis()

        elif self.wifi_started:
            esp_status = self.esp.safely_get_status()

            if esp_status == 3:
                self.set_state(State.ONLINE)

            elif esp_status == 4:
                print(f'Failed to join Wi-Fi network {repr(ssid)}.')
                self.wifi_started = None

            elif not esp_status or cctime.get_millis() > self.wifi_started + 15000:
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
                self.socket_started = cctime.get_millis()
            except Exception as e:
                utils.report_error(e, 'Failed to open socket')
                self.disable_step()

        elif self.esp.socket_connected(self.socket):
            print('Connected!')
            self.set_state(State.CONNECTED)

        elif self.socket_started and cctime.get_millis() > self.socket_started + 15000:
            print('No connection after 15 seconds; retrying.')
            self.close_step()

        elif self.esp.safely_get_status() != 3:
            print('Wi-Fi network lost.')
            self.disable_step()

    def send_step(self, data):
        if self.esp.socket_connected(self.socket):
            self.esp.socket_write(self.socket, data)
        else:
            self.set_state(State.ONLINE)

    def receive_step(self, count):
        if self.esp.socket_connected(self.socket):
            available = self.esp.socket_available(self.socket)
            print('avail', available)
            if available:
                return self.esp.socket_read(self.socket, count)
            else:
                return b''
        else:
            self.set_state(State.ONLINE)
            return b''

    def close_step(self):
        if self.esp and self.socket:
            try:
                self.esp.socket_close(self.socket)
                print('Closed socket.')
            except Exception as e:
                utils.report_error(e, 'Failed to close socket')
        self.socket = None
        self.socket_started = None
        if self.esp and self.esp.safely_get_status() == 3:
            self.set_state(State.ONLINE)
        else:
            self.set_state(State.OFFLINE)

    def disable_step(self):
        self.close_step()
        if self.esp:
            self.esp.deinit()
            self.esp = None
        if self.spi:
            self.spi.deinit()
            self.spi = None
        print('Disabled Wi-Fi.')
        self.set_state(State.OFFLINE)
