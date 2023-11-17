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

    def go(self, url, req_etag=None):
        self.ssl, self.host, self.path = utils.split_url(url)
        self.req_etag = req_etag
        if not self.host:
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
                    raise StopIteration(self.resp_etag)
            else:
                self.silence_started = now
        else:
            self.silence_started = None

    def connect_read(self):
        self.net.step()
        if self.net.state == 'OFFLINE':
            self.net.join()
        elif self.net.state == 'ONLINE':
            # connect() will raise if it fails; there's no risk of a retry loop
            self.net.connect(self.host, ssl=self.ssl)
        elif self.net.state == 'CONNECTED':
            etag = utils.to_bytes(self.req_etag or b'')
            utils.log(f'Fetching {self.path} from {self.host} (ETag {etag}).')
            self.net.send(
                b'GET ' + utils.to_bytes(self.path) + b' HTTP/1.1\r\n' +
                b'Host: ' + utils.to_bytes(self.host) + b'\r\n' +
                b'Connection: Close\r\n' +
                (b'If-None-Match: "' + etag + b'"\r\n' if etag else b'') +
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
            utils.log(f'HTTP status: {status}')
            if status == b'304':
                raise StopIteration(304)
            if status != b'200' and status != b'301' and status != b'302':
                raise ValueError(f'HTTP status {status}')
            self.content_length = -1
            self.resp_etag = None
            self.read = self.http_headers_read

    def http_headers_read(self):
        self.net.step()
        crlf = self.buffer.find(b'\r\n')
        self.check_silence_timeout(crlf < 0)
        if crlf > 0:
            colon = self.buffer.find(b':')
            if 0 < colon < crlf:
                key = bytes(self.buffer[:colon]).lower()
                value = utils.to_str(bytes(self.buffer[colon + 1:crlf])).strip()
                if key == b'content-length':
                    self.content_length = int(value)
                if key == b'etag':
                    self.resp_etag = value.strip('"')
                if key == b'location':
                    self.net.close()
                    utils.log(f'Redirection: {value}')
                    if value.startswith('http:') or value.startswith('https:'):
                        self.go(value)
                    elif value.startswith('/'):
                        self.path = value
                        self.start()
                    else:
                        self.path = self.path.rsplit('/', 1)[0] + '/' + value
                        self.start()
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
            raise StopIteration(self.resp_etag)
        if len(self.buffer):
            chunk = self.buffer[:PACKET_LENGTH]
            self.buffer[:PACKET_LENGTH] = b''
            self.received_length += len(chunk)
            return bytes(chunk)
        chunk = self.net.receive(PACKET_LENGTH)
        self.received_length += len(chunk)
        self.check_silence_timeout(len(chunk) == 0)
        return chunk
