import cctime
from network import State
import prefs
import utils

# Wait this long after Wi-Fi is connected to attempt a fetch.
INITIAL_DELAY = 1000

# If the remote server has stopped sending data for this many milliseconds,
# assume the HTTP response is finished.
SILENCE_TIMEOUT = 10000

# To limit memory use, we read this many bytes from the network at a time.
PACKET_LENGTH = 1500 - 20 - 20  # 1500 - IP header (20) - TCP header (20)


class HttpFetcher:
    def __init__(self, network, url):
        self.network = network
        self.url = url
        self.ssl, self.hostname, self.path = utils.split_url(url)
        self.online_started = None
        self.silence_started = None

        self.buffer = bytearray()
        # Calling read() returns anywhere from zero to PACKET_LENGTH bytes; a
        # zero-byte result does not indicate EOF.  StopIteration indicates EOF.
        self.read = self.connect_read

    def check_silence_timeout(self, is_silent):
        now = cctime.get_millis()
        if is_silent:
            if self.silence_started:
                silence = int(now - self.silence_started)
                if silence > SILENCE_TIMEOUT:
                    print(f'Closing connection after {silence} s of silence.')
                    self.network.close_step()
                    raise StopIteration
            else:
                self.silence_started = now
        else:
            self.silence_started = None

    def connect_read(self):
        if not self.hostname:
            raise ValueError(f'Invalid URL: {self.url}')
        if self.network.state == State.OFFLINE:
            self.online_started = None
            self.network.enable_step(
                prefs.get('wifi_ssid'),
                prefs.get('wifi_password')
            )
        if self.network.state == State.ONLINE:
            if not self.online_started:
                self.online_started = cctime.get_millis()
            if cctime.get_millis() > self.online_started + INITIAL_DELAY:
                self.network.connect_step(self.hostname, ssl=self.ssl)
        if self.network.state == State.CONNECTED:
            self.read = self.request_read
        return b''

    def request_read(self):
        if self.network.state == State.CONNECTED:
            print(f'Fetching {self.path} from {self.hostname}.')
            self.network.send_step(
                b'GET ' + utils.to_bytes(self.path) + b' HTTP/1.1\r\n' +
                b'Host: ' + utils.to_bytes(self.hostname) + b'\r\n' +
                b'Connection: Close\r\n' +
                b'\r\n'
            )
            self.read = self.http_status_read
        return b''

    def http_status_read(self):
        data = self.network.receive_step(PACKET_LENGTH)
        self.buffer.extend(data)
        crlf = self.buffer.find(b'\r\n')
        self.check_silence_timeout(crlf < 0)
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
        self.check_silence_timeout(double_crlf < 0)
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
            print(f'Received {len(chunk)} bytes.')
            return bytes(chunk)
        if self.network.state == State.CONNECTED:
            chunk = self.network.receive_step(PACKET_LENGTH)
            self.check_silence_timeout(len(chunk) == 0)
            print(f'Received {len(chunk)} bytes.')
            return chunk
        else:
            print('Remote server closed connection.')
            self.network.close_step()
            raise StopIteration
