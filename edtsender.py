import edtpacket
import threading

files = "sadasasdsd"
socket.socket()
socket.bind()

dddress = (ip,port)
controltype ={'1':1,'2':0}
txbuffer = [] # Keeps data sent by application but not acknowledged by peer yet
rxbuffer = [] # Keeps data received from peer and not received by application yet


fsmstate = "CLOSED" #initially the connection is closed, 
#"SND_CONNECTED" for single-directed connection from sender to the receiver (i.e., sender can send data to the receiver)


# Receiving window parameters
rcv_ini = 1  # Initial ack number
rcv_nxt = None # Next seq to be received
rcv_wnd = 4096

#sending window parameters
snd_ini = 1 #Initial seq number
snd_mss = 1024
snd_wnd = snd_mss #sending window size for control use

tx_retransmit_timeout_counter = {}  # Keeps track of the timestamps for the sent out packets, used to determine when to retransmit packet
rx_retransmit_request_counter = {}  # Keeps track of us sending 'fast retransmit request' packets so we can limit their count to 2

event_connect = threading.Semaphore(0)  # Used to inform CONNECT syscall that connection related event happened
event_rx_buffer = threading.Semaphore(0)  # USed to inform RECV syscall that there is new data in buffer ready to be picked up
lock_fsm = threading.RLock()  # Used to ensure that only single event can run FSM at given time
lock_rx_buffer = threading.Lock()  # Used to ensure only single event has access to RX buffer at given time
lock_tx_buffer = threading.Lock()  # Used to ensure only single event has access to TX buffer at given time

closing = False  # Indicates that CLOSE syscall is in progress, this lets to finish sending data before FIN packet is transmitted
ooo_packet_queue = {}  # Out of order packet buffer


fsmstate = "CLOSED" #initially the connection is closed, 
# "SND_CONNECTED" for a harf connection from the sender to the receiver (i.e., sender can send data to the receiver)
# "CONNECTED" for a full connection between the sender and the receiver

def connection_coontrol_set():
	print ("1 for reiable connection and 0 for connectionless")
	ans = input()
	if ans == 1:
		connectiontype = 1
	print ("1 for ")
	print ("1 for reiability control")
	#read from inputs
	return connectiontype, controltype



# def packetgeneration(packettype,controltype,data):

# 	return bytes


def ConnectionCreate(connectiontype, address):
	success = False

	if success
		return True

def Data_transmission(controltype, address):

	return True


def connection_close(connectiontype, address):

	return True



def transmit_data():
#send out data segment from TX buffer using sliding window mechanism
	