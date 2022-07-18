from network import State
from utils import to_bytes

# To limit memory use, we read this many bytes from the network at a time.
PACKET_LENGTH = 1500 - 20 - 20  # 1500 - IP header (20) - TCP header (20)


class HttpFetcher:
    def __init__(self, network, prefs, hostname, path):
        self.network = network
        self.prefs = prefs
        self.hostname = hostname
        self.path = path

        self.buffer = bytearray()
        # Calling read() returns anywhere from zero to PACKET_LENGTH bytes; a
        # zero-byte result does not indicate EOF.  StopIteration indicates EOF.
        self.read = self.connect_read

    def connect_read(self):
        if self.network.state == State.OFFLINE:
            self.network.enable_step(
                self.prefs.get('wifi_ssid'),
                self.prefs.get('wifi_password')
            )
        if self.network.state == State.ONLINE:
            self.network.connect_step(self.hostname)
        if self.network.state == State.CONNECTED:
            self.read = self.request_read
        return b''

    def request_read(self):
        if self.network.state == State.CONNECTED:
            self.network.send_step(
                b'GET ' + to_bytes(self.path) + b' HTTP/1.1\r\n' +
                b'Host: ' + to_bytes(self.hostname) + b'\r\n' +
                b'Connection: Close\r\n' +
                b'\r\n'
            )
            self.read = self.http_status_read
        return b''

    def http_status_read(self):
        self.buffer.extend(self.network.receive_step(PACKET_LENGTH))
        crlf = self.buffer.find(b'\r\n')
        if crlf < 0:
            return b''
        words = bytes(self.buffer[:crlf]).split(b' ')
        if words[1] != b'200':
            raise ValueError(f'HTTP status {words[1]}')
        self.read = self.http_headers_read
        return self.read(True)

    def http_headers_read(self, skip_receive=False):
        if not skip_receive:
            self.buffer.extend(self.network.receive_step(PACKET_LENGTH))
        double_crlf = self.buffer.find(b'\r\n\r\n')
        if double_crlf < 0:
            # Keep the last 4 bytes so we don't miss the b'\r\n\r\n' sequence.
            self.buffer[:-4] = b''
            return b''
        self.buffer[:double_crlf + 4] = b''
        self.read = self.content_read
        return self.read()

    def content_read(self):
        if len(self.buffer):
            chunk = self.buffer[:PACKET_LENGTH]
            self.buffer[:PACKET_LENGTH] = b''
            return bytes(chunk)
        if self.network.state == State.CONNECTED:
            return self.network.receive_step(PACKET_LENGTH)
        else:
            self.network.close_step()
            raise StopIteration
