#!/usr/bin/env python3

from src.edpsocket import *
import sys

rcv_ip = sys.argv[1]
rcv_port = int(sys.argv[2])
filename = sys.argv[3]
address = (rcv_ip, rcv_port)


f = open(filename,'rb')
data_tosend = f.read()
print("length of data: ", len(data_tosend))
connection_type = 1 # reliable connection
snd_socket = edpsocket()
connected = snd_socket.connect(connectiontype=connection_type, address=address)
if connected:
	print("connected")
	snd_socket.send(data_tosend)
print("Finish Sending")
snd_socket.close()