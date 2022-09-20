import socket as socklib

from socket import SOCK_DGRAM, getaddrinfo


class socket:
    def __init__(self, type):
        self.sock = socklib.socket(type=type)

    def connect(self, addr, conntype=None):
        return self.sock.connect(addr)

    def settimeout(self, timeout):
        self.sock.settimeout(timeout)

    def send(self, packet):
        return self.sock.send(packet)

    def recv_into(self, packet):
        return self.sock.recv_into(packet)

    def close(self):
        return self.sock.close()
