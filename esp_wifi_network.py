from adafruit_esp32spi import adafruit_esp32spi as esp32spi
from adafruit_esp32spi import adafruit_esp32spi_socket as socket
import board
import cctime
from digitalio import DigitalInOut, Direction
from network import Network, State
import utils


class EspWifiNetwork(Network):
    def __init__(self):
        self.esp = esp32spi.ESP_SPIcontrol(
            board.SPI(),
            DigitalInOut(board.ESP_CS),
            DigitalInOut(board.ESP_BUSY),
            DigitalInOut(board.ESP_RESET)
        )
        self.firmware_version = self.esp.firmware_version
        self.mac_address = self.esp.MAC_address
        # Don't set esp._debug!  It causes UDP to stop working. :(

        self.wifi_started = None
        self.socket = None
        self.connect_started = None
        self.set_state(State.OFFLINE)

    def get_firmware_version(self):
        return str(bytes(self.firmware_version), 'ascii')

    def get_hardware_address(self):
        return ':'.join('%02x' % byte for byte in self.mac_address)

    def set_state(self, new_state):
        self.state = new_state
        utils.log(f'Network is now {self.state}.')

    def enable_step(self, ssid, password):
        ssid = utils.to_bytes(ssid)
        password = utils.to_bytes(password)
        if not self.wifi_started:
            utils.log(f'Joining Wi-Fi network {repr(ssid)}.')
            # NOTE: ssid and password must be bytes, not str!
            self.esp.wifi_set_passphrase(ssid, password)
            self.wifi_started = cctime.get_millis()

        elif self.wifi_started:
            if self.esp.status == esp32spi.WL_CONNECTED:
                self.set_state(State.ONLINE)
                socket.set_interface(self.esp)
                cctime.ntp_sync(socket, 'pool.ntp.org')

            elif cctime.get_millis() > self.wifi_started + 20000:
                utils.log('No Wi-Fi network joined after 20 seconds; retrying.')
                self.esp.disconnect()
                self.esp.wifi_set_passphrase(ssid, password)
                self.wifi_started = cctime.get_millis()

    def connect_step(self, hostname, port=None, ssl=True):
        if self.socket is None:
            self.socket = self.esp.get_socket()
            port = port or (443 if ssl else 80)
            mode = self.esp.TLS_MODE if ssl else self.esp.TCP_MODE
            utils.log(f'Connecting to {hostname} port {port}')
            try:
                # NOTE: hostname must be str, not bytes!
                self.esp.socket_open(self.socket, hostname, port, mode)
                self.connect_started = cctime.get_millis()
            except Exception as e:
                utils.report_error(e, 'Failed to open socket')
                self.esp.reset()
                self.socket = None
                self.set_state(State.OFFLINE)

        elif self.esp.socket_connected(self.socket):
            self.set_state(State.CONNECTED)

        elif cctime.get_millis() > self.connect_started + 10000:
            utils.log('No connection after 10 seconds; retrying.')
            self.close_step()

        elif self.esp.status != 3:
            utils.log('Wi-Fi network lost.')
            self.close_step()
            self.set_state(State.OFFLINE)

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
            return b''

    def close_step(self):
        if self.socket:
            try:
                self.esp.socket_close(self.socket)
                utils.log('Closed socket.')
            except Exception as e:
                utils.report_error(e, 'Failed to close socket')
        if self.state == State.CONNECTED:
            self.set_state(State.ONLINE)
        self.socket = None
