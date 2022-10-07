import cctime
import socket
import ssl
from ssl import _create_unverified_context as create_ssl_context


class UnixNetwork:
    def __init__(self, ssid, password, wifi_connect_delay=1000):
        self.ssid = ssid
        self.password = password

        self.firmware_version = 'None'
        self.mac_address = '00:00:00:00:00:00'

        self.initialized = False
        self.initialize_delay = 1000
        self.initialize_time = None
        self.wifi_connect_delay = wifi_connect_delay
        self.wifi_connect_time = None
        self.socket = None
        self.set_state('OFFLINE')

    def set_state(self, new_state):
        self.state = new_state
        print(f'Network is now {self.state}.')

    def enable(self, ssid, password):
        now = cctime.get_millis()

        if not self.initialized:
            if self.initialize_time:
                if now > self.initialize_time:
                    self.initialized = True
                    self.initialize_time = None
            else:
                self.initialize_time = now + self.initialize_delay

        elif self.state == 'OFFLINE':
            if self.wifi_connect_time:
                if now > self.wifi_connect_time:
                    self.wifi_connect_time = None
                    self.set_state('ONLINE')
                    simulate_ntp_sync()
            elif ssid == self.ssid and password == self.password:
                self.wifi_connect_time = now + self.wifi_connect_delay

    def connect(self, host, port=None, ssl=True):
        port = port or (443 if ssl else 80)
        print(f'Connecting to', host, 'port', port)
        sock = socket.create_connection((host, port))
        if ssl:
            context = create_ssl_context()
            sock = context.wrap_socket(sock, server_hostname=host)
        self.socket = sock
        self.set_state('CONNECTED')

    def send(self, data):
        if self.socket:
            self.socket.send(data)

    def receive(self, count):
        if self.socket:
            data = self.socket.recv(count)
            if len(data) == 0:
                self.close()
            return data

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.set_state(State.ONLINE)


def simulate_ntp_sync():
    import time
    cctime.set_millis(int(time.time() * 1000))
