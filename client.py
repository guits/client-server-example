import socket
import logging
import sys
from lock import _Lock

HOST = '127.0.0.1'
PORT = 65431


class Client:
    def __init__(self,
                 host='',
                 port=22,
                 server=None):
        self.lock = _Lock()
        self.host = host
        self.port = port
        self.log = logging.getLogger(__name__)
        self.log_handler = logging.StreamHandler()
        self.log_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.log.setLevel(logging.DEBUG)
        self.log_handler.setFormatter(self.log_format)
        self.log.addHandler(self.log_handler)

    def get_data(self, socket):
        while True:
            try:
                data = socket.recv(1024)
            except OSError as e:
                self.log.info(f"Connection closed by {self.host}:{self.port}: {e}")
                break
            try:
                data_str = self.decode_data(data)
            except UnicodeDecodeError:
                data_str = str(data)
            self.log.info(f"Received data from "
                          f"{self.host}:{self.port}: {data_str}")

    def run(self, server=None):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                self.socket = s
                s.connect((self.host,
                           self.port))
            except ConnectionRefusedError:
                self.log.error(f"Connection refused to {self.host}:{self.port}")
                sys.exit(1)
            self.log.info(f"Connected to {self.host}:{self.port}")
            self.lock.release()
            while True:
                try:
                    data = s.recv(1024)
                except OSError as e:
                    self.log.info(f"Connection closed by {self.host}:{self.port}: {e}")
                if not data:
                    server.lock.acquire()
                    break
                try:
                    data_str = self.decode_data(data)
                except UnicodeDecodeError:
                    data_str = str(data)
                self.log.info("Received data from "
                              f"{self.host}:{self.port}: {data_str}")
                # send data to client (connected to the frontend)
                # need to make sure the server has accepted a connection before
                # (addressed with Thread.Lock())
                server.to_client(data)

    def send_data(self, data):
        self.log.info(f"Sending data to {self.host}:{self.port}: {data}")
        self.socket.sendall(data.encode("utf-8"))

    def send_raw_data(self, data):
        self.lock.acquire()
        self.log.info(f"Sending data to {self.host}:{self.port}: {data}")
        self.socket.sendall(data)
        self.lock.release()

    def decode_data(self, data):
        return data.decode("utf-8").strip()
