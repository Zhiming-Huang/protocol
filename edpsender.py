import edtpacket
import threading
import time

files = "sadasasdsd"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

addresses = (ip,port)
controltype ={'1':1,'2':0}
txbuffer = [] # Keeps data sent by application but not acknowledged by peer yet
rxbuffer = [] # Keeps data received from peer and not received by application yet
#uakbuffer = [] #keeps track the packet that is not acknowledged

fsmstate = "CLOSED" #initially the connection is closed, 
#"SND_CONNECTED" for single-directed connection from sender to the receiver (i.e., sender can send data to the receiver)


DELAYED_ACK_DELAY = xxx
PACKET_RETRANSMIT_TIMEOUT
timers = {}


# Receiving window parameters
rcv_ini = 1  # Initial ack number
rcv_nxt = None # Next seq to be received
rcv_wnd = 4096

#sending window parameters
snd_ini = 0 #Initial seq number
snd_nxt = snd_ini #the next seq number to send
snd_mss = 1024
snd_max = snd_ini
snd_wnd = snd_mss #sending window size for control use
snd_una = snd_ini #seq not yet acknowledged by peer
tx_buffer_seq_mod = snd_ini #Used to help translate local_seq_send and snd_una numbers to TX buffer pointers

tx_retransmit_timeout_counter = {}  # Keeps track of the timestamps for the sent out packets, used to determine when to retransmit packet
rx_retransmit_request_counter = {}  # Keeps track of us sending 'fast retransmit request' packets so we can limit their count to 2

event_connect = threading.Semaphore(0)  # Used to inform CONNECT syscall that connection related event happened
event_rx_buffer = threading.Semaphore(0)  # USed to inform RECV syscall that there is new data in buffer ready to be picked up
lock_fsm = threading.RLock()  # Used to ensure that only single event can run FSM at a given time
lock_socket = threading.RLock() #used to ensure that only singe event can use socket at a given time
lock_rx_buffer = threading.Lock()  # Used to ensure only single event has access to RX buffer at given time
lock_tx_buffer = threading.Lock()  # Used to ensure only single event has access to TX buffer at given time


closing = False  # Indicates that CLOSE syscall is in progress, this lets to finish sending data before FIN packet is transmitted
ooo_packet_queue = {}  # Out of order packet buffer


fsmstate = "CLOSED" #initially the connection is closed, 
# "SEMI_CONNECTED" for a harf connection from the sender to the receiver (i.e., sender can send data to the receiver)
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
	if connectiontype == 0:
		return True
	edp_fsm(syscall="CONNECT")
	event_connect.acquire()
	return fsmstate == "SEMI_CONNECTED" or fsmstate == "CONNECTED"

def Data_transmission(controltype, address):

	return True


def connection_close(connectiontype, address):

	return True

######################### The followings are codes for FSM ############################## 

def transmit_packet(seq=None,packet_type=None,flag_fin=False,controltype={}, data=''):
	#send out data segment from TX buffer using sliding window mechanism

	global snd_nxt,snd_max,timers,timeout
	
	seq = seq if seq else snd_nxt
	flag_ctl = packet_type == 1 or packet_type == 3 or packet_type ==5 or packet_type == 7
	flag_ack = packet_type == 2 or packet_type == 3 or packet_type ==6 or packet_type == 7
	ack = rcv_nxt if flag_ack else 0 
	packet_to_send = edppacket(packet_type = 1,seq)
	if ack:
		edppacket.setack(ack)
	edppacket.set_controltype = controltype
	packet_to_send.packet2bytes()
	with lock_socket:
		s.sendto(packet_to_send,address)
	snd_nxt = seq + len(data) + flag_ctl +flag_fin
	snd_max = max(snd_max,snd_nxt)
	tx_buffer_seq_mod += flag_ctl + flag_fin

	#In case packet caries FIN flag make note of its SEQ number
	if flag_fin:
		snd_fin = snd_nxt

	# If in (SEMI-)CONNECTION state then reset ACK delay timer
	if fsmstate == "SEMI_CONNECTED":
		timeout = DELAYED_ACK_DELAY

	# If packet contains data then Initialize / adjust packet's retransmit counter and timer
	if data or flag_ctl or flag_fin:
		tx_retransmit_timeout_counter[seq] = tx_retransmit_timeout_counter.get(seq, -1) + 1
		timers[seq] = PACKET_RETRANSMIT_TIMEOUT * (1 << tx_retransmit_timeout_counter[seq])
	return packet_to_send




def tranmit_data():
	if fsmstate == "CTL_SENT" and snd_nxt == snd_ini: #check if we need to (re)send inital control packet
		packet_to_send = transmit_packet(packet_type = 1)
		_control_sent_process(packet_to_send)
		return


	if fsmstate in {"SEMI_CONNECTED"}: #check if we are in the state that allows sending data out
		remaining_data_len = len(tx.buffer) - tx_buffer_nxt


	if fsmstate in {"CLOSE_WAIT"}:#check if we need to (re)transmit the final fin packet

def _control_sent_process(packet):
	if _process_ack_packet(packet)
		event_connect.release()


	_retransmt_packet_timeout()

def _process_ack_packet(packet):
	snd_una = max(snd_una,packet.ack)


def _retransmt_packet_timeout():
	global fsmstate
	if snd_una in tx_retransmit_timeout_counter and timers(snd_una):
		if tx_retransmit_timeout_counter[snd_una] == PACKET_RETRANSMIT_MAX_COUNT:
			#If in any state with established connection connection inform socket about connection failure




def edp_fsm(packet=None, syscall = None, main_thread = False):
	#process event
	with lock_fsm:
		return {
		"CLOSED": _edp_fsm_closed,
		"CTL_SENT": _edp_fsm_CTL_SND,
		"CTL_RCVD": _edp_fsm_CTL_RCVD,
		"SEMI_CONNECTED": _edp_fsm_SEMI_CONNECTED,
		"CLOSE_WAIT": _edp_fsm_SEMI_CONNECTED
		}[fsmstate](packet,syscall,main_thread)

def _edp_fsm_closed(packet,syscall,main_thread):
	global fsmstate
	if syscall == "CONNECT":
		fsmstate = "CTL_SENT"

def _edp_fsm_CTL_SND(packet,syscall,main_thread):
	if main_thread == True
    transmit_data()


def _edp_fsm_CTL_RCVD(packet,syscall,main_thread):
	global fsmstate
	fsmstate = "SEMI_CONNECTED"
	
	if syscall == 0:
		print(3)
	else:
		print(5)


def  _edp_fsm_SEMI_CONNECTED(packet,syscall,main_thread):
	global fsmstate
	fsmstate = "CTL_RCVD"
	if syscall == 0:
		print(4)
	else:
		print(6)


def run_fsm():
	while True:
		time.sleep(0.01)
		timeout -= 1
		edp_fsm(main_thread=True)

###### the followings are some funcitons to assist contol machanisms #############
def tx_buffer_nxt():
	return max(snd_nxt - tx_buffer_seq_mod,0)

def tx_buffer_una():
	return max(snd_una - tx_buffer_seq_mod,0)

threading.Thread(target=run_fsm).start()


