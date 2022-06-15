class State:
    OFFLINE = 'OFFLINE'  # networking is disabled
    ONLINE = 'ONLINE'  # connected to the Internet, but not to any host
    CONNECTED = 'CONNECTED'  # connected to a host, ready to send or receive


class Network:
    """Non-blocking API for network operations.  Each *_step method should
    aim to finish within 10 ms.  If the operation is incomplete, the state
    will be unchanged and the client can call the same method again.
    """

    # Implementations should shadow this with an instance variable.
    state = State.OFFLINE

    def __init__(self):
        """Sets the initial state to OFFLINE."""
        raise NotImplementedError('Network is an abstract interface')

    def enable_step(self, ssid, password):
        """In state OFFLINE, connects to the Internet, resulting in state
        OFFLINE (call again) or ONLINE."""
        raise NotImplementedError

    def connect_step(self, hostname, ssl=True):
        """In state ONLINE, establishes a TCP or SSL connection, resulting in
        state ONLINE (call again) or CONNECTED (ready to send or receive)."""
        raise NotImplementedError

    def send_step(self, data):
        """In state CONNECTED, writes data (as bytes) to the current
        connection, resulting in state CONNECTED (ready to send or receive
        data) or ONLINE (other side has closed the connection)."""
        raise NotImplementedError

    def receive_step(self, count):
        """In state CONNECTED, reads and returns up to 'count' bytes from the
        current connection, resulting in state CONNECTED (ready to send or
        receive more data) or ONLINE or OFFLINE."""
        raise NotImplementedError

    def close_step(self):
        """In state CONNECTED, closes the connected socket, resulting in
        state ONLINE."""
        raise NotImplementedError

    def disable_step(self):
        """In any state, shuts down and releases all networking resources,
        resulting in state OFFLINE."""
        raise NotImplementedError
