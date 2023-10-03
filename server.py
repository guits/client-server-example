import socket
import sys
import logging
import time
from threading import Thread
from client import Client

HOST = "127.0.0.1"  # Standard loopback interface address (localhost)
PORT = 65431  # Port to listen on (non-privileged ports are > 1023)


class Server:
    def __init__(self,
                 host='127.0.0.1',
                 port=65431):
        self.ready = False
        self.host = host
        self.port = port
        self.log = logging.getLogger(__name__)
        self.log_handler = logging.StreamHandler()
        self.log_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        self.log.setLevel(logging.DEBUG)
        self.log_handler.setFormatter(self.log_format)
        self.log.addHandler(self.log_handler)
        self.thread = Thread(target=self.run)
        self.log.info("Server initialized with host: "
                      f"{self.host} and port: {self.port}")

    def find_port(self, socket, addr, port):
        _port = port
        while _port < port+150:
            try:
                socket.bind((addr, _port))
                return _port
            except OSError:
                _port += 1
        raise OSError("No free port available")

    def handle_client(self, client, addr):
        with client:
            self._client = client
            while True:
                data = client.recv(1024)
                if not data:
                    self.log.info(f"[*] Connection closed by {addr[0]}:{addr[1]}")
                    self.ready = False
                    client.close()
                    break
                try:
                    data_str = self.decode_data(data)
                except UnicodeDecodeError:
                    data_str = str(data)
                self.log.info("Received data from "
                              f"{addr[0]}:{addr[1]}: {data_str}")
                if data_str == 'exit':
                    self.log.info(f"Closing connection with "
                                  f"{addr[0]}:{addr[1]}")
                    client.close()
                    sys.exit(0)
                # send data to endpoint
                # self.client.send_data(f"{data_str}\n\n")
                self.client.send_raw_data(data)

    def accept(self, socket):
        self.log.info("Waiting for a connection...")
        client, addr = socket.accept()
        self.log.info(f"Accepted connection from: {addr[0]}:{addr[1]}")
        self.client = Client(host='hive.abrioux.info', port=22)
        self.client_thread = Thread(target=self.client.run,
                                    kwargs={"server": self})
        self.client_thread.start()
        self.thread = Thread(target=self.handle_client,
                             kwargs={"client": client,
                                     "addr": addr})
        self.thread.start()
        self.ready = True

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.port = self.find_port(s, self.host, self.port)
            s.listen()
            self.log.info(f"Listening on {self.host}:{self.port}")
            while True:
                self.accept(s)

    def decode_data(self, data):
        return data.decode("utf-8").strip()
