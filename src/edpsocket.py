from src.edppacket import *
import threading
import numpy as np
import time
import socket

PACKET_RETRANSMIT_MAX_COUNT = 3 # If data is not acked, the maxi time to resend
PACKET_RETRANSMIT_TIMEOUT = 300 # Time to retransmit a packet if ACK not received
TIME_INTERVAL = 0.1

class edpsocket:
	def __init__(self, local_ip_address=None, local_port=None, remote_ip_address=None, remote_port=None):
		self.seqlist = [] #save seq sent for data plotting
		self.version = 1  #the version of edp
		self.ctr_length = 1
		self.controltype = [2,1]
		self.noerrorctl = 0 if 1 == self.controltype[0] else 1 #
		self.txbuffer = [] # Keeps data sent by application but not acknowledged by peer yet
		self.rxbuffer = [] # Keeps data received from peer and not received by application yet
		#uakbuffer = [] #keeps track the packet that is not acknowledged
		self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.fsmstate = "CLOSED" #initially the connection is closed, 
		#"SND_CONNECTED" for single-directed connection from sender to the receiver (i.e., sender can send data to the receiver)
		self.address = None #remote address

		self.local_ip_address= None
		self.local_port = None
		if local_ip_address!=None and local_port != None:
			self.udpsocket.bind((local_ip_address,local_port))

		self.connectiontype = {}
		self.DELAYED_ACK_DELAY = 1
		#self.PACKET_RETRANSMIT_TIMEOUT = 200
		self.FINWAIT = 200
		self.timers = {}
		self.delayed_ack_timer = self.DELAYED_ACK_DELAY
		self.flag_fin = False
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
		self.snd_ewn = self.snd_mss #Effective window size, used as simple congestion management mechanism
		self.snd_fin = None  # Seq of FIN packet
	    #receiving window parameters
		self.rcv_ini = 0 #Initial seq number
		self.rcv_nxt = 0 #Next seq to be received
		self.rcv_una = 0 #seq we acked
		self.rcv_mss = 1024 #maximum segment size
		self.rcv_wnd = 65535 # window size
		self.rcv_wsc = 1 # Window scale


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
		threading.Thread(target=self.run_fsm).start() #start the finite state machine for edp
		threading.Thread(target=self.rx_edp).start() #keep receiving packets

		self.fsmstate = "CLOSED" #initially the connection is closed, 
		# "SEMI_CONNECTED" for a harf connection from the sender to the receiver (i.e., sender can send data to the receiver)
		# "CONNECTED" for a full connection between the sender and the receiver



	def listen(self):
		self.edp_fsm(syscall = "LISTEN")
		self.event_connect.acquire()
		return self.fsmstate == "SEMI_CONNECTED" 

	def connection_coontrol_set(self,controltype):
		self.controltype = controltype
		#read from inputs
		return True

	# def packetgeneration(packettype,controltype,data):



	def connect(self,connectiontype, address):
		self.address = address
		self.connectiontype = connectiontype
		if connectiontype == 0:
			return True
		self.edp_fsm(syscall="CONNECT")
		self.event_connect.acquire()
		print("Connected with fsmstate: %s"%self.fsmstate)
		return self.fsmstate == "SEMI_CONNECTED" or self.fsmstate == "CONNECTED"

	def send(self,data):
		if self.fsmstate in {"SEMI_CONNECTED","CONNECTED"}:
			with self.lock_tx_buffer:
				self.txbuffer.extend(list(data))
				return len(data)
		return None


	def receive(self,byte_count = None):
		self.event_rx_buffer.acquire() # wait till there is any data in the buffer

		if not self.rxbuffer and self.fsmstate == "CLOSED":
			return None
		with self.lock_rx_buffer:
			if byte_count is None:
				byte_count = len(self.rxbuffer)
			else:
				byte_count = min(byte_count,len(self.rxbuffer))

			rxbuffer = self.rxbuffer[:byte_count]
			del self.rxbuffer[:byte_count]

			#if there is any data left or closed connection then release the rx_buffer event
			if self.rxbuffer:
				self.event_rx_buffer.release()
		return bytes(rxbuffer)


	def close(self):
		#close syscall
		self.edp_fsm(syscall = "CLOSE")
		return None

	def control_modify(self, connectiontype):
		if self.fsmstate in {"SEMI_CONNECTED","CONNECTED"}:
			self.connectiontype = connectiontype
			self.edp_fsm(syscall = "CTL_UPDATE")

	######################### The followings are codes for FSM ############################## 
	def _enqueue_rx_buffer(self,data):
		with self.lock_rx_buffer:
			self.rxbuffer.extend(list(data))
    		#if rx_buffer event has not been released yet (it could be released if some data were sitting in buffer already) then release it
			if not self.event_rx_buffer._value:
				self.event_rx_buffer.release()



	def _edp_fsm_listen(self,packet,syscall,main_thread):
		#if got an ctl packet, send ack packet to establish a half connection
		if packet and packet.packet_type & 0b010:
			self.address = packet.source_address
			self.snd_mss = 1024
			self.snd_wnd = packet.wnd * self.snd_wsc
			self.snd_wsc = packet.wscale if None else 1 # if peer does not support window scaling, then set it to 1
			self.snd_ewn = self.snd_mss
			self.rcv_nxt = 1
			self.fsmstate = "CTL_RCVD"
			self._transmit_packet(packet_type=0b001)
			return
		if syscall == "CLOSE":
			self.fsmstate = "CLOSED"
			return 

	def _edp_fsm_CTL_RCV(self,packet,syscall,main_thread):
		if self.fsmstate == "CTL_UPDATE_CFM":
			if main_thread:
				self._transmit_data(flag_ack=True)

			if packet:
				if packet.packet_type == 0b001:
					print("Updating Confirmed, go back to SEMI_CONNECTED state!")
					self._process_ack_packet(packet)
					self.fsmstate = "SEMI_CONNECTED"


		else:
		# for main_thread, resend ACK if its timer expired
			if packet:
				#print("Packet receive")
				if packet.packet_type & 0b010: #if receive ctl again, which means the former ack is not received
					self._transmit_packet(packet_type=0b001)


			if packet and packet.packet_type & 0b100: #if received a data packet
				if packet.seq == self.rcv_nxt:
					self.fsmstate = "SEMI_CONNECTED"
					self._process_ack_packet(packet)
					self.event_connect.release()


	def _edp_fsm_CLOSE_RCV(self,packet,syscall,main_thread):
		if packet and packet.flags == 1:
			if self.flag_fin == False:
				self.rcv_nxt += 1
				self.flag_fin = True
			self._transmit_packet(packet_type=0b001)
			self.FINWAIT = 20
			return
		if main_thread:
			self.FINWAIT -= 1
			if self.FINWAIT <= 0:
				self.fsmstate = "CLOSED"
				np.save("receive_seq_list.npy",self.seqlist)
				self.FINWAIT = 20



	def _transmit_packet(self,seq=None,packet_type=None,flag_fin=False, data='',flag_rst=False):
		#send out data segment from TX buffer using sliding window mechanism

		#global snd_nxt,snd_max,timers,timeout
		
		seq = seq if seq else self.snd_nxt
		flag_ctl = (packet_type & 0b010) >0
		flag_ack = (packet_type & 0b001) >0
		ack = self.rcv_nxt if flag_ack else 0
		packet_to_send = edppacket(version= self.version, packet_type = packet_type)
		if flag_ctl:
			#ctr_length = len(self.controltype.keys())
			#print(ctr_length)
			packet_to_send.set_ctr_header(ctr_length=self.ctr_length, ctr_mech=self.controltype)
		if flag_ack:
			fin = 1 if flag_fin else 0
			fin = int(fin)
			#print("fin",fin)
			packet_to_send.set_ack_header(ack=self.rcv_nxt, wnd=self.rcv_wnd - len(self.rxbuffer), flags= fin , mMTU=self.rcv_mss)

		if data:
			if seq not in self.seqlist:
				self.seqlist.append(seq)
			packet_to_send.set_data_header(seq=seq, data_length=len(data), DAT=data)
			#packet_to_send.generate_checksum()

		packet_to_send.packet2bytes()
		with self.lock_socket:
			self.udpsocket.sendto(packet_to_send.raw,self.address)
		self.rcv_una = self.rcv_nxt
		if not self.flag_fin:
			self.snd_nxt = seq + len(data) + (1  if flag_ctl else 0 )+ (1 if flag_fin else 0)
		self.flag_fin = flag_fin
		print("snd_nxt: ",self.snd_nxt)
		self.snd_max = max(self.snd_max,self.snd_nxt)
		self.tx_buffer_seq_mod += flag_ctl + flag_fin

		#In case packet caries FIN flag make note of its SEQ number
		if flag_fin:
			self.snd_fin = self.snd_nxt
			print("flag_fin flags:",packet_to_send.flags)

		# If in (SEMI-)CONNECTION state then reset ACK delay timer
		if self.fsmstate == "SEMI_CONNECTED":
			self.delayed_ack_timer = self.DELAYED_ACK_DELAY
		# 	self.timeout = self.DELAYED_ACK_DELAY

		# If packet contains data then Initialize / adjust packet's retransmit counter and timer
		if data or flag_ctl or flag_fin:
			self.tx_retransmit_timeout_counter[seq] = self.tx_retransmit_timeout_counter.get(seq, -1) + 1
			self.timers[seq] = PACKET_RETRANSMIT_TIMEOUT * (1 << self.tx_retransmit_timeout_counter[seq])
		return packet_to_send




	def _transmit_data(self,flag_ack=False):
		#close_sent = False
		# add data to the send buffer
		# if self.fsmstate == "CTL_SENT" and self.snd_nxt == self.snd_ini: #check if we need to (re)send inital control packet
		# 	packet_to_send = self._transmit_packet(packet_type = 0b010)
		# 	return


		if self.fsmstate in {"SEMI_CONNECTED"}: #check if we are in the state that allows sending data out
			remaining_data_len = len(self.txbuffer) - self.tx_buffer_nxt
			usable_window = self.snd_ewn - self.tx_buffer_nxt
			transmit_data_len = min(self.snd_mss, usable_window, remaining_data_len)
			print("transmit data length,", self.snd_nxt,transmit_data_len)
			if remaining_data_len:
				if transmit_data_len:
					with self.lock_tx_buffer:
						transmit_data = self.txbuffer[self.tx_buffer_nxt:self.tx_buffer_nxt + transmit_data_len]
					#print (transmit_data)
					if flag_ack:
						self._transmit_packet(packet_type = 0b101,data=bytes(transmit_data))
					else:
						self._transmit_packet(packet_type = 0b100,data=bytes(transmit_data))
					return

		if self.fsmstate == "CTL_RCVD" and self.snd_nxt == self.snd_ini:
			self._transmit_packet(packet_type = 0b001)


		# if self.fsmstate in {"CLOSE_SENT"}:#check if we need to (re)transmit the final fin packet
		# 	self._transmit_packet(packet_type = 0b001, flag_fin = True)
			#close_sent = True
	# def _control_sent_process(self,packet):
	# 	if self._process_ack_packet()
	# 		self.event_connect.release()


	# 	self._retransmt_packet_timeout()

	def _process_ack_packet(self,packet):
		# process data/ack packet when the connection is established
		if packet.packet_type & 0b001:
			self.snd_una = max(self.snd_una,packet.ack) #record the local seq that has been acked by peer
			if self.snd_nxt < self.snd_una <= self.snd_max:
				self.snd_nxt = self.snd_una

			#Purge acked data from TX buffer
			with self.lock_tx_buffer:
				del self.txbuffer[: self.tx_buffer_una]
			self.tx_buffer_seq_mod += self.tx_buffer_una
			#if packet.packet_type & 0b100: () 
			#self.rcv_nxt
			#update remote window size
			if self.snd_wnd != packet.wnd * self.snd_wsc:
				self.snd_wnd = packet.wnd * self.snd_wsc

			self.snd_ewn = min(self.snd_ewn << 1, self.snd_wnd)

			#purge expired tx packet retransmit request
			for seq in list(self.tx_retransmit_request_counter):
				if seq < packet.ack:
					self.tx_retransmit_request_counter.pop(seq)

			#purge expired tx packet retransmit timeouts
			for seq in list(self.tx_retransmit_timeout_counter):
				if seq < packet.ack:
					self.tx_retransmit_timeout_counter.pop(seq)
					self.timers.pop(seq)

		if packet.packet_type & 0b100: #if packet is a data packet
			self.rcv_nxt = packet.seq + len(packet.DAT)
			if packet.seq not in self.seqlist:
				self.seqlist.append(packet.seq)
			self._enqueue_rx_buffer(packet.DAT)

			#purge expired rx retransmit requests
			for seq in list(self.rx_retransmit_request_counter):
				if seq < self.rcv_nxt:
					self.rx_retransmit_request_counter.pop(seq)

			#Bring next packet from ooo_paket_queue if available
			packet = self.ooo_packet_queue.pop(self.rcv_nxt,None)
			if packet:
				self.edp_fsm(packet)
			if self.rcv_nxt > 14000:
				self.control_modify([1,2,2,1])
		
	def _delayed_ack(self):
        #Run Delayed ACK mechanism
		if self.delayed_ack_timer <= 0:
			if self.rcv_nxt > self.rcv_una:
				self._transmit_packet(packet_type=0b001)
			self.delayed_ack_timer = self.DELAYED_ACK_DELAY

	def _retransmt_packet_timeout(self):
		#global fsmstate
		if self.snd_una in self.tx_retransmit_timeout_counter:
			if self.timers[self.snd_una] <= 0:
			#if the unacknowledged packet is timeout
				if self.tx_retransmit_timeout_counter[self.snd_una] == PACKET_RETRANSMIT_MAX_COUNT:
				#If in any state with established connection connection inform socket about connection failure
					self._transmit_packet(flag_rst=True,packet_type=0b001)
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
			"LISTEN": self._edp_fsm_listen,
			"CTL_RCVD": self._edp_fsm_CTL_RCV,
			"CTL_SENT": self._edp_fsm_CTL_SND,
			"SEMI_CONNECTED": self._edp_fsm_SEMI_CONNECTED,
			"CTL_UPDATE_SENT": self._edp_fsm_CTL_SND,
			"CTL_UPDATE_CFM": self._edp_fsm_CTL_RCV,
			"CLOSE_SENT": self._edp_fsm_CLOSE_SND,
			"CLOSE_RCV": self._edp_fsm_CLOSE_RCV
			}[self.fsmstate](packet,syscall,main_thread)




	def _edp_fsm_closed(self,packet,syscall,main_thread):
		if syscall == "CONNECT":
			self.fsmstate = "CTL_SENT"

		if syscall == "LISTEN":
			self.fsmstate = "LISTEN"



	def _edp_fsm_CTL_SND(self,packet,syscall,main_thread):
		if self.fsmstate == "CTL_UPDATE_SENT":
			if main_thread:
				_transmit_packet(packet_type=0b011)
				time.sleep(10)

			if packet:
				if packet_type & 0b100 and packet_type & 0b001:
					self.fsmstate = "SEMI_CONNECTED" #Actually now it is in the fully connected stage
					self.edp_fsm(packet)

		else:
			if main_thread == True:
				self._retransmt_packet_timeout()
				self._transmit_packet(packet_type=0b010)
				return

		    # If we get an ack packet 
			if packet:
				#print(packet.packet_type & 0b001)
				if packet.packet_type & 0b001:
					print("Received: ",packet.ack,self.snd_nxt)
					if packet.ack == self.snd_nxt:
						if packet.packet_type & 0b010:
			    			# if got a ctl from peer, then transit to full_connected
							self._transmit_packet(packet_type=0b001)
							self.fsmstate = "Full_Connected"
						else:
							self.fsmstate ="SEMI_CONNECTED"
						self.event_connect.release()

	    # If we get RST + ACK packet, change state to closed

	    #if we get syscall to close, then change the state to closed
		if syscall == "CLOSE":
			self.fsmstate = "CLOSED"



	#def _edp_fsm_CTL_UPDATE_CFM(self,packet,syscall,main_thread):


	def  _edp_fsm_SEMI_CONNECTED(self,packet,syscall,main_thread):
		#the main_thread event -> send out data and run mechanisms such as delayd ack mechanism
		if main_thread:
			self._retransmt_packet_timeout()
			self._transmit_data()
			if not self.noerrorctl:
				self._delayed_ack()
			print("Remaining data to send:",len(self.txbuffer))
			if self.closing and not self.txbuffer: #if finish sending out all data
				self.fsmstate = "CLOSE_SENT"
        

		if packet and packet.packet_type & 0b001: #if got ACK packet
			print("got ack", packet.ack, self.snd_nxt)
			if not (packet.packet_type & 0b010) and not (packet.flags == 1): #if the ack packet is not ctl or fin packet
         		#suspected retransmission request -> reset TX window and local seq number
				if packet.ack == self.snd_una and not (packet.packet_type & 0b100):
					print(packet.flags)
					self._retransmit_packet_request(packet)
					return
				if self.snd_una <= packet.ack <= self.snd_max:
					self._process_ack_packet(packet)
					return
			if packet.packet_type & 0b010:
				self.controltype = packet.ctr_mech
				self.noerrorctl = 0 if 1 == self.controltype[0] else 1
				self.fsmstate = "CTL_UPDATE_CFM"




		if packet and (packet.packet_type & 0b100): #if got data packet
         			#to be finished in the receiver side
			if packet.seq > self.rcv_nxt: #got a higher seq than we expected
				self.ooo_packet_queue[paket.seq] = packet
				self.rx_retransmit_request_counter[self.rcv_nxt] = self.rx_retransmit_request_counter.get(self.rcv_nxt,0) + 1
				if self.rx_retransmit_request_counter[self.rcv_nxt] <= 2:
					self._transmit_packet(packet_type = 0b001)
				return


			if packet.seq == self.rcv_nxt or self.noerrorctl: #regular packets
				self._process_ack_packet(packet)
				return
			return

		if packet and packet.flags==1: #receive a packet with the fin field set
			self.fsmstate = "CLOSE_RCV"
			self._process_ack_packet(packet)
			self._transmit_packet(packet_type = 0b001)


         #Got CLOSE syscall -> Send FIN packet
		if syscall == "CLOSE":
			self.closing = True
			#print("CLOSED Send")
			return

		if syscall == "CTL_UPDATE":
			self.noerrorctl = 0 if 1 == self.controltype[0] else 1
			print("SENT CONTROL UPDATE!")
			self.fsmstate = "CTL_UPDATE_SENT"




         			# self.snd_wnd = packet.win * self.snd_wsc
         			# self.snd_ewn = self.snd_mss
         			# self._process_ack_packet(packet)

	def _edp_fsm_CLOSE_SND(self,packet,syscall,main_thread):
		#If it is in main_thread, transmit FIN packet
		if main_thread:
			self._retransmt_packet_timeout()
			self._transmit_packet(packet_type = 0b001, flag_fin = True)
			return

		if packet and (packet.packet_type & 0b001): #receive ACK
			#print("123213123: ", self.snd_una, packet.ack, self.snd_max)
			if self.snd_una <=packet.ack<=self.snd_max:
				self._process_ack_packet(packet)
				if packet.ack >= self.snd_fin:
					self.fsmstate = "CLOSED"
					np.save("send_seq_list.npy",self.seqlist)




	def _retransmit_packet_request(self,packet):
    	#retransmit packet after receiving request from peer
		self.tx_retransmit_request_counter[packet.ack] = self.tx_retransmit_request_counter.get(packet.ack,0)+1
		if self.tx_retransmit_request_counter[packet.ack] > 1:
			self.snd_nxt = self.snd_una


	# def _delayed_ack(self):
	# #run delayed ack mechanism
	# 	if timers[1] == 0:
	# 		if self.rcv_nxt > self.rcv_una		


	def run_fsm(self):
		while True:
			print(self.fsmstate)
			time.sleep(TIME_INTERVAL)
			self.delayed_ack_timer -= 1
			for name in self.timers:
				self.timers[name] -= 1
			self.edp_fsm(main_thread=True)

	
	###### the followings are some funcitons to assist contol machanisms #############
	@property
	def tx_buffer_nxt(self):
		return max(self.snd_nxt - self.tx_buffer_seq_mod,0)

	@property
	def tx_buffer_una(self):
        #'snd_una' number relative to TX buffer
		return max(self.snd_una - self.tx_buffer_seq_mod, 0)


	def  rx_edp(self):
    #this function is used to receive packets
		while True:
			data_stream,address=self.udpsocket.recvfrom(2048)
			#print(data_stream)
			packet = edppacket(1, None)
			packet.bytes2packet(data_stream)
			#print(packet.packet_type)
			packet.source_address = address
			self.edp_fsm(packet=packet)
	


