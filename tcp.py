#!/usr/bin/env python

import socket
import time
TCP_IP = '127.0.0.1'
TCP_PORT = 8301
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
while 1:
    time.sleep(1)
    conn.send(bytes(''.encode('utf-8')))
conn.close()