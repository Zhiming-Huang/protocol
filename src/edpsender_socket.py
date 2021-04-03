import edtpacket
import threading
import time

PACKET_RETRANSMIT_MAX_COUNT = 3 # If data is not acked, the maxi time to resend
PACKET_RETRANSMIT_TIMEOUT = 1000 # Time to retransmit a packet if ACK not received


class edpsender_socket(self):
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#addresses = (ip,port)
	self.controltype = {'1':1,'2':0}
	self.txbuffer = [] # Keeps data sent by application but not acknowledged by peer yet
	self.rxbuffer = [] # Keeps data received from peer and not received by application yet
	#uakbuffer = [] #keeps track the packet that is not acknowledged
	self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	self.fsmstate = "CLOSED" #initially the connection is closed, 
	#"SND_CONNECTED" for single-directed connection from sender to the receiver (i.e., sender can send data to the receiver)
	self.address = None
	self.connectiontype = {}
	self.DELAYED_ACK_DELAY = 200
	self.PACKET_RETRANSMIT_TIMEOUT = 200
	self.timers = {}

	#print("transmit finished")
	#sending window parameters
	self.snd_ini = 0 #Initial seq number
	self.snd_nxt = self.snd_ini #the next seq number to send
	self.snd_mss = 1024
	self.snd_max = self.snd_ini
	self.snd_wnd = self.snd_mss #sending window size for control use
	self.snd_wsc = 1 #sending window scale
	self.snd_una = self.snd_ini #seq not yet acknowledged by peer
	self.tx_buffer_seq_mod = self.snd_ini #Used to help translate local_seq_send and snd_una numbers to TX buffer pointers
    self.snd_ewn = self.snd_mss # Effective window size, used as simple congestion management mechanism



	self.tx_retransmit_timeout_counter = {}  # Keeps track of the timestamps for the sent out packets, used to determine when to retransmit packet
	self.rx_retransmit_request_counter = {}  # Keeps track of us sending 'fast retransmit request' packets so we can limit their count to 2
	self.tx_retransmit_request_counter = {}  # Keeps track of DUP packets sent from peer to determine if any of them is a retransmit request

	self.event_connect = threading.Semaphore(0)  # Used to inform CONNECT syscall that connection related event happened
	self.event_rx_buffer = threading.Semaphore(0)  # USed to inform RECV syscall that there is new data in buffer ready to be picked up
	self.lock_fsm = threading.RLock()  # Used to ensure that only single event can run FSM at a given time
	self.lock_socket = threading.RLock() #used to ensure that only singe event can use socket at a given time
	self.lock_rx_buffer = threading.Lock()  # Used to ensure only single event has access to RX buffer at given time
	self.lock_tx_buffer = threading.Lock()  # Used to ensure only single event has access to TX buffer at given time


	self.closing = False  # Indicates that CLOSE syscall is in progress, this lets to finish sending data before FIN packet is transmitted
	self.ooo_packet_queue = {}  # Out of order packet buffer
	threading.Thread(target=run_fsm).start()
	threading.Thread(target=rx_edp).start() #keep receiving packets

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


	def connect(self,connectiontype, address):
		self.address = address
		self.connectiontype = connectiontype
		if connectiontype == 0:
			return True
		edp_fsm(syscall="CONNECT")
		self.event_connect.acquire()
		return self.fsmstate == "SEMI_CONNECTED" or self.fsmstate == "CONNECTED"

	def send(self,data):
		if self.fsmstate in {"SEMI_CONNECTED","CONNECTED"}:
			with self.lock_tx_buffer:
				self.tx_buffer.extend(list(data))
				return len(data)
		return None


	def close(self):
		#close syscall
		self.tcp_fsm(syscall = "CLOSE")
		return None

	def control_modify(self, connectiontype):
		if self.fsmstate in {"SEMI_CONNECTED","CONNECTED"}:
			self.connectiontype = connectiontype
			self.tcp_fsm(syscall = "CTL_UPDATE")

	######################### The followings are codes for FSM ############################## 

	def _transmit_packet(self,seq=None,packet_type=None,flag_fin=False,controltype={}, data=''):
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
		if data:
			checksum = self.checksum(data)
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




	def transmit_data(self):
		# add data to the send buffer
		if self.fsmstate == "CTL_SENT" and self.snd_nxt == self.snd_ini: #check if we need to (re)send inital control packet
			packet_to_send = _transmit_packet(packet_type = 1)
			return


		if fsmstate in {"SEMI_CONNECTED"}: #check if we are in the state that allows sending data out
			remaining_data_len = len(tx.buffer) - tx_buffer_nxt
			usable_window = self.snd_ewn - self.tx_buffer_nxt
			transmit_data_len = min(self.snd_mss, usable_window, remaining_data_len)
			if remaining_data_len:
				if transmit_data_len:
					with self.lock_tx_buffer:
						transmit_data = self.tx_buffer(self.tx_buffer_nxt:self.tx_buffer_nxt + transmit_data_len)
					self._transmit_packet(packet_type = 3)
					return


		if fsmstate in {"CLOSE_SENT"}:#check if we need to (re)transmit the final fin packet
			self._transmit_packet(packet_type = 1, flag_fin = True)
	# def _control_sent_process(self,packet):
	# 	if self._process_ack_packet()
	# 		self.event_connect.release()


	# 	self._retransmt_packet_timeout()

	def _process_ack_packet(self,packet):
		# process data/ack packet when the connection is established
		self.snd_una = max(snd_una,packet.ack) #record the local seq that has been acked by peer
		if self.snd.nxt < self.snd_una <= self.snd_max:
			self.snd_nxt = self.snd_una

		#Purge acked data from TX buffer
		with self.lock_tx_buffer:
			del self.tx_buffer[: self.tx_buffer_una]
		self.tx_buffer_seq_mod += self.tx_buffer_una
		#if packet.packet_type & 0b100: () 
		#self.rcv_nxt
		#update remote window size
		if self.snd_wnd != packet.win * self.snd_wsc:
			self.sndwnd = packet.win * self.snd_wsc

		#purge expired tx packet retransmit request
		for seq in list(self.tx_retransmit_request_counter):
			if seq < packet.ack:
				self.tx_retransmit_request_counter.pop(seq)

		#purge expired tx packet retransmit timeouts
		for seq in list(self.tx_retransmit_timeout_counter):
			if seq < packet.ack:
				self.tx_retransmit_timeout_counter.pop(seq)

		


	def _retransmt_packet_timeout(self):
		#global fsmstate
		if self.snd_una in self.tx_retransmit_timeout_counter and timers(self.snd_una) == 0:
			#if the unacknowledged packet is timeout
			if self.tx_retransmit_timeout_counter[self.snd_una] == self.PACKET_RETRANSMIT_MAX_COUNT:
				#If in any state with established connection connection inform socket about connection failure
				self._transmit_packet(flag_rst=True,flag_ack = True)
				if self.fsmstate in {"SEMI_CONNECTED","CLOSE_SENT"}:
					self.event_rx_buffer.release()
				if self.fsmstate == "CTL_SENT":
					SELF.event_connect.release()
				self.fsmstate = "CLOSED"

			self.snd_ewn = self.snd_mss
			self.snd_nxt = self.snd_una

			if self.snd_nxt == self.snd_ini or self.snd_nxt == self.snd_fin:
				self.tx_buffer_seq_mod -= 1
			return


	def edp_fsm(self,packet=None, syscall = None, main_thread = False):
		#process event
		with self.lock_fsm:
			return {
			"CLOSED": self._edp_fsm_closed,
			"CTL_SENT": self._edp_fsm_CTL_SND,
			"SEMI_CONNECTED": self._edp_fsm_SEMI_CONNECTED,
			"CLOSE_SENT": self._edp_fsm_CLOSE_SND
			}[self.fsmstate](packet,syscall,main_thread)




	def _edp_fsm_closed(self,packet,syscall,main_thread):
		if syscall == "CONNECT":
			self.fsmstate = "CTL_SENT"



	def _edp_fsm_CTL_SND(self,packet,syscall,main_thread):
		if main_thread == True:
			self._retransmt_packet_timeout()
	    	self.transmit_data()

	    # If we get an ack packet 
	    if packet and self.packet_type & 0b001:
	    	if packet.ack == self.snd_nxt:
	    		if self.packet_type & 0b010:
	    			# if got a ctl from peer, then transit to full_connected
	    			self.transmit_packet(packet_type=0b001)
	    			self.fsmstate = "Full_Connected"
	    		else:
	    			self.fsmstate ="SEMI_CONNECTED"
	    		self.event_connect.release()

	    # If we get RST + ACK packet, change state to closed

	    #if we get syscall to close, then change the state to closed
	    if syscall == "CLOSE":
	    	self.fsmstate = "CLOSED"
	     


	def _edp_fsm_CLOSE_SND(self,packet,syscall,main_thread):
		#If it is in main_thread, transmit FIN packet
		if main_thread:
			self._retransmt_packet_timeout()
			self._transmit_data()
			return

		if package and packet_type & 0b001: #receive ACK
			if self.snd_una <=packet.ack<=self.snd_max:
				self._process_ack_packet(packet)
				if packet.ack >= self.snd_fin:
					self.fsmstate = "CLOSED"



	def  _edp_fsm_SEMI_CONNECTED(self,packet,syscall,main_thread):
		#the main_thread event -> send out data and run mechanisms such as delayd ack mechanism
		if main_thread:
			self._retransmt_packet_timeout()
			self._transmit_data()
			#self._delayed_ack()
			if self.closing and not self.tx_buffer: #if finish sending out all data
				self.fsmstate = "CLOSE_SENT"
        

        if packet and packet.packet_type & 0b001: #if got ACK packet
         	if not packet.packet_type & 0b010 and not packet.fin: #if the ack packet is not ctl or fin packet
         		#suspected retransmission request -> reset TX window and local seq number
         		if packet.ack == self.snd_una:
         			self._retransmit_packet_request(packet)
         			return
         		if self.snd_una <= packet.ack <= self.snd_max:
         			self._process_ack_packet(packet)
         			return

         if packet and packet.packet_type & 0b100: #if got data packet
         			#to be finished in the receiver side
         	return


         #Got CLOSE syscall -> Send FIN packet
         if syscall == "CLOSE":
         	self.closing = True
         	return



         			# self.snd_wnd = packet.win * self.snd_wsc
         			# self.snd_ewn = self.snd_mss
         			# self._process_ack_packet(packet)




    def _retransmit_packet_request(self,packet):
    	#retransmit packet after receiving request from peer
    	self.tx_retransmit_timeout_counter[packet.ack] = self.tx_retransmit_timeout_counter.get(packet.ack,0)+1
    	if self.tx_retransmit_request_counter[packet.ack] > 1:
    		self.snd_nxt = self.snd_una


	# def _delayed_ack(self):
	# #run delayed ack mechanism
	# 	if timers[1] == 0:
	# 		if self.rcv_nxt > self.rcv_una		


	def run_fsm(self):
		while True:
			time.sleep(0.01)
			for name in self.timers:
				self.timers[name] -= 1
			edp_fsm(main_thread=True)

	
	###### the followings are some funcitons to assist contol machanisms #############
	@property
	def tx_buffer_nxt(self):
		return max(self.snd_nxt - self.tx_buffer_seq_mod,0)

    @property
    def tx_buffer_una(self):
        """ 'snd_una' number relative to TX buffer """

        return max(self.snd_una - self.tx_buffer_seq_mod, 0)


    def  rx_edp(self):
    #this function is used to receive packets
    	while True:
    		data_stream,address:=self.udpsocket.recvfrom(2048)
    		packet = edppacket(1.0, None)
    		packet.bytes2packet(data_stream)
    		self.edp_fsm(packet=packet)



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
	


