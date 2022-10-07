import cctime
import prefs
import utils

# If the remote server has stopped sending data for this many milliseconds,
# assume the HTTP response is finished.
SILENCE_TIMEOUT = 10000

# To limit memory use, we read this many bytes from the network at a time.
PACKET_LENGTH = 1500 - 20 - 20  # 1500 - IP header (20) - TCP header (20)


class HttpFetcher:
    def __init__(self, net):
        self.net = net
        self.buffer = bytearray()

    def go(self, url):
        self.ssl, self.hostname, self.path = utils.split_url(url)
        if not self.hostname:
            raise ValueError(f'Invalid URL: {url}')
        self.start()

    def start(self):
        self.buffer[:] = b''
        self.silence_started = None
        # Calling read() returns anywhere from zero to PACKET_LENGTH bytes, or
        # None; b'' or None does not indicate EOF.  StopIteration indicates EOF.
        self.read = self.connect_read

    def check_silence_timeout(self, is_silent):
        now = cctime.monotonic_millis()
        if is_silent:
            if self.silence_started:
                silence = int(now - self.silence_started)
                if silence > SILENCE_TIMEOUT:
                    utils.log(f'Closing socket after {silence} s of silence.')
                    self.net.close()
                    raise StopIteration
            else:
                self.silence_started = now
        else:
            self.silence_started = None

    def connect_read(self):
        self.net.step()
        if self.net.state == 'OFFLINE':
            self.net.join(prefs.get('wifi_ssid'), prefs.get('wifi_password'))
        elif self.net.state == 'ONLINE':
            # connect() will raise if it fails; there's no risk of a retry loop
            self.net.connect(self.hostname, ssl=self.ssl)
        elif self.net.state == 'CONNECTED':
            utils.log(f'Fetching {self.path} from {self.hostname}.')
            self.net.send(
                b'GET ' + utils.to_bytes(self.path) + b' HTTP/1.1\r\n' +
                b'Host: ' + utils.to_bytes(self.hostname) + b'\r\n' +
                b'Connection: Close\r\n' +
                b'\r\n'
            )
            self.read = self.http_status_read

    def http_status_read(self):
        self.net.step()
        data = self.net.receive(PACKET_LENGTH)
        self.buffer.extend(data)
        crlf = self.buffer.find(b'\r\n')
        self.check_silence_timeout(crlf < 0)
        if crlf > 0:
            status = bytes(self.buffer[:crlf]).split(b' ')[1]
            self.buffer[:crlf + 2] = b''
            if status != b'200' and status != b'301' and status != b'302':
                raise ValueError(f'HTTP status {status}')
            self.content_length = -1
            self.read = self.http_headers_read

    def http_headers_read(self):
        self.net.step()
        crlf = self.buffer.find(b'\r\n')
        self.check_silence_timeout(crlf < 0)
        if crlf > 0:
            colon = self.buffer.find(b':')
            if 0 < colon < crlf:
                key = self.buffer[:colon].lower()
                value = self.buffer[colon + 1:crlf].strip()
                if key == b'location':
                    self.net.close()
                    loc = utils.to_str(bytes(value))
                    utils.log(f'Redirection: {loc}')
                    if loc.startswith('http:') or loc.startswith('https:'):
                        self.go(loc)
                    elif loc.startswith('/'):
                        self.path = loc
                        self.start()
                    else:
                        self.path = self.path.rsplit('/', 1)[0] + '/' + loc
                        self.start()
                if key == b'content-length':
                    self.content_length = int(value)
            self.buffer[:crlf + 2] = b''
        elif crlf == 0:
            self.buffer[:2] = b''
            self.received_length = 0
            self.read = self.content_read
        else:
            self.buffer.extend(self.net.receive(PACKET_LENGTH))

    def content_read(self):
        self.net.step()
        if (self.received_length >= self.content_length > 0 or  # file completed
            self.net.state != 'CONNECTED'):  # server closed the connection
            raise StopIteration
        if len(self.buffer):
            chunk = self.buffer[:PACKET_LENGTH]
            self.buffer[:PACKET_LENGTH] = b''
            self.received_length += len(chunk)
            return bytes(chunk)
        chunk = self.net.receive(PACKET_LENGTH)
        self.received_length += len(chunk)
        self.check_silence_timeout(len(chunk) == 0)
        return chunk
