from network import Network, State
import socket
import ssl
import time

class UnixNetwork(Network):
    def __init__(self, ssid, password, wifi_connect_delay=5, debug=False):
        self.ssid = ssid
        self.password = password
        self.initialized = False
        self.initialize_delay = 1
        self.initialize_time = None
        self.wifi_connect_delay = wifi_connect_delay
        self.wifi_connect_time = None
        self.socket = None
        self.debug = debug
        self.set_state(State.OFFLINE)

    def set_state(self, new_state):
        self.state = new_state
        if self.debug:
            print(f'Network is now {self.state}.')

    def enable_step(self, ssid, password):
        if not self.initialized:
            if self.initialize_time:
                if time.time() > self.initialize_time:
                    self.initialized = True
                    self.initialize_time = None
            else:
                self.initialize_time = time.time() + self.initialize_delay

        elif self.state == State.OFFLINE:
            if self.wifi_connect_time:
                if time.time() > self.wifi_connect_time:
                    self.wifi_connect_time = None
                    self.set_state(State.ONLINE)
            elif ssid == self.ssid and password == self.password:
                self.wifi_connect_time = time.time() + self.wifi_connect_delay

    def connect_step(self, hostname, port=None, ssl=True):
        port = port or (443 if ssl else 80)
        sock = socket.create_connection((hostname, port))
        if ssl:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=hostname)
        self.socket = sock
        self.set_state(State.CONNECTED)

    def send_step(self, data):
        if self.socket:
            self.socket.send(data)

    def receive_step(self):
        if self.socket:
            data = self.socket.recv(1024)
            if len(data) == 0:
                self.set_state(State.ONLINE)
            return data

    def close_step(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.set_state(State.ONLINE)

    def disable_step(self):
        self.set_state(State.OFFLINE)
        self.initialized = False
