from udp_socket import *

newudpsocket = udp_socket()
print(newudpsocket.socket_id())
newudpsocket.bind("124.1.1.1", 8888)