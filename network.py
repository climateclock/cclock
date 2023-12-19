from adafruit_esp32spi import adafruit_esp32spi as esp32spi
from adafruit_esp32spi import adafruit_esp32spi_socket as socklib
import board
import cctime
import digitalio
import prefs
import utils


def init():
    esp = esp32spi.ESP_SPIcontrol(
        board.SPI(),
        digitalio.DigitalInOut(board.ESP_CS),
        digitalio.DigitalInOut(board.ESP_BUSY),
        digitalio.DigitalInOut(board.ESP_RESET)
    )
    socklib.set_interface(esp)
    return Network(esp, socklib)


class Network:
    def __init__(self, esp, socklib):
        self.esp = esp
        self.socklib = socklib
        self.firmware_version = str(bytes(self.esp.firmware_version), 'ascii')
        self.mac_address = ':'.join('%02x' % b for b in self.esp.MAC_address)
        # Don't set esp._debug!  It causes UDP to stop working. :(

        self.socket = None
        self.set_state('OFFLINE')
        self.indicator = utils.null_context

    def set_state(self, new_state):
        # Possible states are:
        #     OFFLINE (inactive)
        #     JOINING (trying to join a Wi-Fi network)
        #     ONLINE (connected to a Wi-Fi network, but not to any host)
        #     CONNECTED (connected to an HTTP server)
        self.state = new_state
        self.state_started = cctime.monotonic_millis()
        self.state_elapsed = 0
        utils.log(f'Network is now {self.state}.')

    def step(self):
        self.state_elapsed = cctime.monotonic_millis() - self.state_started

        if self.state == 'JOINING':
            if self.esp.status == 3:
                self.set_state('ONLINE')
                ntp_server = prefs.get('ntp_server')
                cctime.ntp_sync(self.socklib, ntp_server)

            elif self.state_elapsed > 20000:
                utils.log(f'Could not join Wi-Fi network after 20 s; retrying.')
                self.esp.disconnect()
                self.join()
            return

        if (self.state == 'ONLINE' or self.state == 'CONNECTED'
            ) and self.esp.status != 3:
            utils.log('Wi-Fi network lost.')
            self.close()

        if (self.state == 'CONNECTED' and
            not self.esp.socket_connected(self.socket)):
            utils.log('Remote server closed connection.')
            self.close()

    def join(self):
        ssid = utils.to_bytes(prefs.get('wifi_ssid'))
        password = utils.to_bytes(prefs.get('wifi_password'))
        if ssid:
            self.set_state('JOINING')
            utils.log(f'Joining Wi-Fi network {repr(ssid)}.')
            # NOTE: ssid and password must be bytes, not str!
            self.esp.wifi_set_passphrase(ssid, password)
        else:
            self.set_state('OFFLINE')
            utils.log(f'Wi-Fi is disabled because SSID is blank.')

    def connect(self, host, port=None, ssl=True):
        if self.state != 'ONLINE':
            print('Cannot connect() while network is {self.state}.')
            return

        try:
            self.socket = self.esp.get_socket()
        except TimeoutError as e:
            utils.report_error(e, 'Failed to get socket; resetting')
            self.esp.reset()
            self.set_state('OFFLINE')

        port = port or (443 if ssl else 80)
        mode = self.esp.TLS_MODE if ssl else self.esp.TCP_MODE
        with self.indicator:
            utils.log(f'Connecting to {host} port {port}')
            try:
                # NOTE: host must be str, not bytes!
                self.esp.socket_open(self.socket, host, port, mode)
                if self.esp.socket_connected(self.socket):
                    self.set_state('CONNECTED')
            except Exception as e:
                utils.report_error(e, 'Failed to open socket; resetting')
                self.esp.reset()
                self.socket = None
                self.set_state('OFFLINE')

    def send(self, data):
        if self.state == 'CONNECTED':
            self.esp.socket_write(self.socket, data)

    def receive(self, count):
        data = b''
        if self.state == 'CONNECTED' and self.esp.socket_available(self.socket):
            data = self.esp.socket_read(self.socket, count)
            if data == b'':
                print('Server closed connection.')
                self.close()
            print(f'Received {len(data)} bytes.')
        return data

    def close(self):
        if self.socket:
            try:
                self.esp.socket_close(self.socket)
                utils.log('Socket closed.')
            except Exception as e:
                utils.report_error(e, 'Failed to close socket')
        self.socket = None
        self.set_state('ONLINE' if self.esp.status == 3 else 'OFFLINE')
