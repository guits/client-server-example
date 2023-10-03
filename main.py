from server import Server
from client import Client
from threading import Thread
import time

s = Server()
t = Thread(target=s.run)
t.start()
time.sleep(2)
# c = Client(host='hive.abrioux.info', port=7777)
# c.run()
