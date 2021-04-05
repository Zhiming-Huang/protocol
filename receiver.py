import src.edpsocket
import sys




rcv_ip = sys.argv[1]
rcv_port = int(sys.argv[2])
#filename = sys.argv[3]



connection_type = 1 # reliable connection
rcv_socket = edpsocket.edpsocket(local_ip_address=rcv_ip, local_port=rcv_port)
connected = rcv_socket.listen()
if connected:
	with open("./received.html", "wb") as file:
	    while True:
	        reply = rcv_socket.receive(1024)
	        if reply:
	            print(reply)
	            file.write(reply)
	        else:
	            break


rcv_socket.close()