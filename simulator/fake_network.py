from adafruit_esp32spi import adafruit_esp32spi as esp32spi
import cctime
import fake_socklib
import network
import select
import socket
import ssl
from ssl import _create_unverified_context as create_ssl_context
import utils

WIFI_JOIN_DELAY = 2000  # how long it takes to connect to the simulated AP
ap_credentials = None


def install(ap_ssid, ap_password):
    global ap_credentials
    ap_credentials = (utils.to_bytes(ap_ssid), utils.to_bytes(ap_password))
    network.init = init


def init():
    return network.Network(FakeEsp(ap_credentials), fake_socklib)


class FakeEsp:
    """Simulates an instance of ESP_SPIcontrol with a nearby Wi-Fi AP."""

    TCP_MODE = 1
    TLS_MODE = 2

    def __init__(self, ap_credentials):
        self._ap_credentials = ap_credentials
        self.firmware_version = b'None'
        self.MAC_address = b'\x00\x00\x00\x00\x00\x00'
        self.reset()

    def _set_status(self, status):
        self._status = status
        self._status_started = cctime.monotonic_millis()

    def _status_elapsed(self):
        return cctime.monotonic_millis() - self._status_started

    def _step(self):
        if self._status == esp32spi.WL_NO_SSID_AVAIL:
            if self._client_credentials == self._ap_credentials:
                if self._status_elapsed() > WIFI_JOIN_DELAY:
                    self._set_status(esp32spi.WL_CONNECTED)

    def _get_socket_by_id(self, sid):
        if not self._sockets.get(sid):
            raise ValueError(f'No socket with ID {sid}')
        return self._sockets[sid]

    @property
    def status(self):
        self._step()
        return self._status

    def reset(self):
        cctime.sleep_millis(760)  # simulate the time it takes to reset
        self._client_credentials = None
        self._sockets = {}
        self._set_status(esp32spi.WL_IDLE_STATUS)

    def wifi_set_passphrase(self, ssid, password):
        self._client_credentials = (ssid, password)
        self._set_status(esp32spi.WL_NO_SSID_AVAIL)

    def disconnect(self):
        self._client_credentials = None
        self._sockets = {}
        self._set_status(esp32spi.WL_IDLE_STATUS)

    def get_socket(self):
        sid = 1
        while sid in self._sockets:
            sid += 1
        self._sockets[sid] = None
        return sid

    def socket_open(self, sid, hostname, port, mode):
        sock = socket.create_connection((hostname, port), 2)
        if mode == self.TLS_MODE:
            context = create_ssl_context()
            sock = context.wrap_socket(sock, server_hostname=hostname)
        self._sockets[sid] = sock

    def socket_connected(self, sid):
        return bool(self._get_socket_by_id(sid))

    def socket_write(self, sid, data):
        return self._get_socket_by_id(sid).send(data)

    def socket_available(self, sid):
        sock = self._get_socket_by_id(sid)
        r, w, x = select.select([sock], [], [], 0)
        return bool(r)

    def socket_read(self, sid, count):
        data = self._get_socket_by_id(sid).recv(count)
        if data == b'':
            self._sockets[sid] == None
        return data

    def socket_close(self, sid):
        self._get_socket_by_id(sid).close()
        del self._sockets[sid]
