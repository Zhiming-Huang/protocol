import edtpacket
import threading
import time

files = "sadasasdsd"


class edpsender_socket(self):
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#addresses = (ip,port)
	self.controltype = {'1':1,'2':0}
	self.txbuffer = [] # Keeps data sent by application but not acknowledged by peer yet
	self.rxbuffer = [] # Keeps data received from peer and not received by application yet
	#uakbuffer = [] #keeps track the packet that is not acknowledged
	self.udpsocket = socket.socket(socket.AF_INET,cosket.SOCK_DGRAM)
	self.fsmstate = "CLOSED" #initially the connection is closed, 
	#"SND_CONNECTED" for single-directed connection from sender to the receiver (i.e., sender can send data to the receiver)
	self.address = None

	self.DELAYED_ACK_DELAY = 200
	self.PACKET_RETRANSMIT_TIMEOUT = 200
	self.timers = {}

	#print("transmit finished")
	#sending window parameters
	self.snd_ini = 0 #Initial seq number
	self.snd_nxt = snd_ini #the next seq number to send
	self.snd_mss = 1024
	self.snd_max = snd_ini
	self.snd_wnd = snd_mss #sending window size for control use
	self.snd_una = snd_ini #seq not yet acknowledged by peer
	self.tx_buffer_seq_mod = snd_ini #Used to help translate local_seq_send and snd_una numbers to TX buffer pointers

	self.tx_retransmit_timeout_counter = {}  # Keeps track of the timestamps for the sent out packets, used to determine when to retransmit packet
	self.rx_retransmit_request_counter = {}  # Keeps track of us sending 'fast retransmit request' packets so we can limit their count to 2

	self.event_connect = threading.Semaphore(0)  # Used to inform CONNECT syscall that connection related event happened
	self.event_rx_buffer = threading.Semaphore(0)  # USed to inform RECV syscall that there is new data in buffer ready to be picked up
	self.lock_fsm = threading.RLock()  # Used to ensure that only single event can run FSM at a given time
	self.lock_socket = threading.RLock() #used to ensure that only singe event can use socket at a given time
	self.lock_rx_buffer = threading.Lock()  # Used to ensure only single event has access to RX buffer at given time
	self.lock_tx_buffer = threading.Lock()  # Used to ensure only single event has access to TX buffer at given time


	self.closing = False  # Indicates that CLOSE syscall is in progress, this lets to finish sending data before FIN packet is transmitted
	self.ooo_packet_queue = {}  # Out of order packet buffer
	threading.Thread(target=run_fsm).start()

	self.fsmstate = "CLOSED" #initially the connection is closed, 
	# "SEMI_CONNECTED" for a harf connection from the sender to the receiver (i.e., sender can send data to the receiver)
	# "CONNECTED" for a full connection between the sender and the receiver


	def connection_coontrol_set(self):
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


	def ConnectionCreate(self,connectiontype, address):
		self.address = address
		if connectiontype == 0:
			return True
		edp_fsm(syscall="CONNECT")
		self.event_connect.acquire()
		return self.fsmstate == "SEMI_CONNECTED" or self.fsmstate == "CONNECTED"

	def Data_transmission(self,controltype, address):

		return True


	def connection_close(self,connectiontype, address):

		return True

	######################### The followings are codes for FSM ############################## 

	def transmit_packet(self,seq=None,packet_type=None,flag_fin=False,controltype={}, data=''):
		#send out data segment from TX buffer using sliding window mechanism

		#global snd_nxt,snd_max,timers,timeout
		
		seq = seq if seq else self.snd_nxt
		flag_ctl = packet_type == 1 or packet_type == 3 or packet_type ==5 or packet_type == 7
		flag_ack = packet_type == 2 or packet_type == 3 or packet_type ==6 or packet_type == 7
		ack = self.rcv_nxt if flag_ack else 0 
		packet_to_send = edppacket(packet_type = 1,seq)
		if ack:
			packet_to_send.setack(ack)
		packet_to_send.set_controltype = controltype
		#set packets ????
		packet_to_send.packet2bytes()
		with lock_socket:
			s.sendto(packet_to_send.raw,address)
		self.snd_nxt = seq + len(data) + flag_ctl +flag_fin
		self.snd_max = max(snd_max,snd_nxt)
		self.tx_buffer_seq_mod += flag_ctl + flag_fin

		#In case packet caries FIN flag make note of its SEQ number
		if flag_fin:
			self.snd_fin = self.snd_nxt

		# If in (SEMI-)CONNECTION state then reset ACK delay timer
		if fsmstate == "SEMI_CONNECTED":
			self.timeout = self.DELAYED_ACK_DELAY

		# If packet contains data then Initialize / adjust packet's retransmit counter and timer
		if data or flag_ctl or flag_fin:
			tx_retransmit_timeout_counter[seq] = tx_retransmit_timeout_counter.get(seq, -1) + 1
			timers[seq] = PACKET_RETRANSMIT_TIMEOUT * (1 << tx_retransmit_timeout_counter[seq])
		return packet_to_send




	def tranmit_data(self):
		if self.fsmstate == "CTL_SENT" and self.snd_nxt == self.snd_ini: #check if we need to (re)send inital control packet
			packet_to_send = transmit_packet(packet_type = 1)
			_control_sent_process(packet_to_send)
			return


		if fsmstate in {"SEMI_CONNECTED"}: #check if we are in the state that allows sending data out
			remaining_data_len = len(tx.buffer) - tx_buffer_nxt


		if fsmstate in {"CLOSE_WAIT"}:#check if we need to (re)transmit the final fin packet

	def _control_sent_process(self,packet):
		if _process_ack_packet(packet)
			self.event_connect.release()


		_retransmt_packet_timeout()

	def _process_ack_packet(self,packet):
		self.snd_una = max(snd_una,packet.ack)


	def _retransmt_packet_timeout(self):
		#global fsmstate
		if self.snd_una in self.tx_retransmit_timeout_counter and timers(self.snd_una):
			if self.tx_retransmit_timeout_counter[self.snd_una] == self.PACKET_RETRANSMIT_MAX_COUNT:
				#If in any state with established connection connection inform socket about connection failure




	def edp_fsm(self,packet=None, syscall = None, main_thread = False):
		#process event
		with self.lock_fsm:
			return {
			"CLOSED": _edp_fsm_closed,
			"CTL_SENT": _edp_fsm_CTL_SND,
			"CTL_RCVD": _edp_fsm_CTL_RCVD,
			"SEMI_CONNECTED": _edp_fsm_SEMI_CONNECTED,
			"CLOSE_WAIT": _edp_fsm_SEMI_CONNECTED
			}[self.fsmstate](packet,syscall,main_thread)

	def _edp_fsm_closed(self,packet,syscall,main_thread):
		#global fsmstate
		if syscall == "CONNECT":
			self.fsmstate = "CTL_SENT"

	def _edp_fsm_CTL_SND(self,packet,syscall,main_thread):
		if main_thread == True
	    transmit_data()


	def _edp_fsm_CTL_RCVD(self,packet,syscall,main_thread):
		self.fsmstate = "SEMI_CONNECTED"
		
		if syscall == 0:
			print(3)
		else:
			print(5)


	def  _edp_fsm_SEMI_CONNECTED(self,packet,syscall,main_thread):
		self.fsmstate = "CTL_RCVD"
		if syscall == 0:
			print(4)
		else:
			print(6)


	def run_fsm(self):
		while True:
			time.sleep(0.01)
			for name in self.timers:
				self.timers[name] -= 1
			edp_fsm(main_thread=True)

	###### the followings are some funcitons to assist contol machanisms #############
	def tx_buffer_nxt(self):
		return max(self.snd_nxt - self.tx_buffer_seq_mod,0)

	def tx_buffer_una(self):
		return max(self.snd_una - self.tx_buffer_seq_mod,0)

    @staticmethod
    def checksum(source_string):
        my_sum = 0
        count_to = (len(source_string) / 2) * 2
        count = 0
        while count < count_to:
            this_val = ord(source_string[count + 1])*256+ord(source_string[count])
            my_sum += this_val
            count += 2
        if count_to < len(source_string):
            my_sum += ord(source_string[len(source_string) - 1])
        my_sum = (my_sum >> 16) + (my_sum & 0xffff)
        my_sum += (my_sum >> 16)
        answer = ~my_sum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer


	


