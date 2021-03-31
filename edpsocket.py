import random
import socket
import pickle
import threading
import time

DATA_DIVIDE_LENGTH = 1024
DATA_LENGTH = DATA_DIVIDE_LENGTH
SENT_SIZE = DATA_LENGTH + 5000  # Pickled objects take a lot of space
LAST_CONNECTION = -1
FIRST = 0

class edppacket(object):
    def __init__(self):
        self.version = 1.0
        #self.length = 0
        self.type = 0
        self.checksum = 0
        
    def settype(self,type):
        self.type = type
        if type == 1：#control packet
            self.control = {} #control[funcname] = value 
        if type == 2 or type = 6: #ack packet or data+ack
            self.ack = 0
            self.window = 0
            self.fin = 0 
        if type == 3 or type = 6:: #data packet or data+ack
            self.seq = 0
            self.data = ""
    def __repr__(self):
        return "edtpacket"

    def __str__(self):
        return swq
    
    def __cmp__(self,other):
        return cmp(self.seq, other.seq)

class edpsocket(object,timeout = 5):
    def __init__(self):
        self.status = 1 # socket open or closed
        self.own_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket
        self.own_socket.settimeout(timeout)
        self.connections = {}
        self.connection_queue = []
        self.connection_controltype = {}
        self.connection_lock = threading.lock()
        self.queue_lock = threading.lock()
        self.packets_received = {"CTL": {}, "ACK": {}, "CTL-ACK": {}, "DATA or FIN": {}, "FIN-ACK": {}}
    
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

    # conditions = ["CTL", "CTL-ACK", "ACK", "FIN", "FIN-ACK", "DATA"]
    # packet = (packet,
    def sort_answers(self, packet, address):
        if packet.packet_type() == "DATA" or packet.packet_type() == "FIN":
            self.packets_received["DATA or FIN"][address] = packet
        elif packet.packet_type() == "":
            print "redundant packet found", packet
        else:
            self.packets_received[packet.packet_type()][address] = packet

    @staticmethod
    def data_divider(data):
        """Divides the data into a list where each element's length is 1024"""
        data = [data[i:i + DATA_DIVIDE_LENGTH] for i in range(0, len(data), DATA_DIVIDE_LENGTH)]
        data.append("END")
        return data

    def central_receive_handler(self):
        while True and self.status:
            try:
                packet, address = self.own_socket.recvfrom(SENT_SIZE)
                packet = pickle.loads(packet)
                self.sortanswers(packet,address)
            except socket.timeout:
                continue
            except socket.error as error:
                self.own_socket.close()
                self.status=0
                print("An error has occured:socket error %s" %error)

    def central_receive(self):
        t = threading.Thread(target=self.central_receive_handler)
        t.daemon = True
        t.start()

        # conditions = ["SYN", "SYN-ACK", "ACK", "FIN", "FIN-ACK", "DATA"]
    def listen_handler(self, max_connections):
        try:
            while True:
                try:
                    answer, address = self.find_correct_packet("SYN")

                    with self.queue_lock:
                        if len(self.connection_queue) < max_connections:
                            self.connection_queue.append((answer, address))
                        else:
                            self.own_socket.sendto("Connections full", address)
                except KeyError:
                    continue
        except socket.error as error:
            print "Something went wrong in listen_handler func! Error is: %s." + str(error)

    def listen(self, max_connections=1):
        try:
            t = threading.Thread(target=self.listen_handler, args=(max_connections,))
            t.daemon = True
            t.start()
        except Exception as error:
            print "Something went wrong in listen func! Error is: %s." % str(error)
            
    def accept(self):
        try:
            while True:
                if self.connection_queue:
                    with self.queue_lock:
                        answer, address = self.connection_queue.pop()
                    self.connections[address] = edpPacket()
                    if answer.version < edpPacket.version and "3" in answer.control.accept.keys():
                        upgrade_protocol(1, address)
                        return address
                    self.connections[address].ack =  1
                    #self.connections[address].seq += 1
                    #self.connections[address].set_flags(ack=True, syn=True)
                    self.connections[server_address].settype(2)
                    packet_to_send = pickle.dumps(self.connections[address])
                    
                    #lock address, connections dictionary?
                    packet_not_sent_correctly = True
                    while packet_not_sent_correctly or answer is None:
                        try:
                            packet_not_sent_correctly = False
                            self.own_socket.sendto(packet_to_send, address)
                            answer = self.find_correct_packet("ACK", address)
                        except socket.timeout:
                            packet_not_sent_correctly = True
                    self.connections[address].set_flags()
                    self.connections[address].ack = answer.seq + 1
                    return address
        except Exception as error:
            print ("Something went wrong in accept func: " + str(error))
            self.own_socket.close()

    def find_correct_packet(self, condition, address=("Any",)):
        not_found = True
        tries = 0
        while not_found and tries < 2 and self.status:
            try:
                not_found = False
                if address[0] == "Any":
                    order = self.packets_received[condition].popitem()  # to reverse the tuple received
                    return order[1], order[0]
                if condition == "ACK":
                    tries += 1
                return self.packets_received[condition].pop(address)
            except KeyError:
                not_found = True
                time.sleep(0.1)
#The above methods are used for server side, and the following methods are used for client side
#control function "1" for reliability control,
    def connect(self, server_address=("127.0.0.1", 10000), controlfunc = {"1":1,"2":0,"3"：0}):
        try:
            self.connection_controltype[server_address] = controlfunc
            self.connections[server_address] = edtpacket()
            self.connections[server_address].settype(1)
            self.connections[server_address].control=controlfunc
            first_packet_to_send = pickle.dumps(self.connections[server_address])
            self.own_socket.sendto(first_packet_to_send, list(self.connections.keys())[FIRST])
            answer = self.find_correct_packet("CTL-ACK", server_address)
            if type(answer) == str:  # == "Connections full":
                raise socket.error("Server cant receive any connections right now.")
            if answer.version < self.connections[server_address].version and "3" in controlfunc.keys():
                upgrade_protocol(self,server_address)
            self.connections[server_address].settype(2) #send ack to the control packet from the server side
            #self.connections[server_address].ack = answer.seq + 1
            self.connections[server_address].seq += 1 #the next packet received from the server should have seq 1
            #self.connections[server_address].set_flags(ack=True)
            second_packet_to_send = pickle.dumps(self.connections[server_address])
            self.own_socket.sendto(second_packet_to_send, list(self.connections.keys())[FIRST])
            #self.connections[server_address].set_flags()
            return True #if connected successfully, return true
        except socket.error as error:
            print ("Something went wrong in connect func: " + str(error))
            self.own_socket.close()
            raise Exception("The socket was closed")
    
    def upgrade_protocol(self, type, address):


    def listen_handler(self, data, connection):

#The following methods are for both client side and server side
    def send(self, data, connection=None):
        try:
            if connection not in self.connections.keys():
                if connection is None:
                    connection = self.connections.keys()[0]
                else:
                    return "Connection not in connected devices"
            data_parts = edtsocket.data_divider(data)
            for data_part in data_parts:
                data_not_received = True
                checksum_of_data = edtsocket.checksum(data_part)
                self.connections[connection].checksum = checksum_of_data
                self.connections[connection].data = data_part
                self.connections[connection].set_flags()
                packet_to_send = pickle.dumps(self.connections[connection])
                while data_not_received:
                    data_not_received = False
                    try:
                        self.own_socket.sendto(packet_to_send, connection)
                        answer = self.find_correct_packet("ACK", connection)

                    except socket.timeout:
                        print "timeout"
                        data_not_received = True
                self.connections[connection].seq += len(data_part)
        except socket.error as error:
            print "Socket was closed before executing command. Error is: %s." % error

    def recv(self, connection=None):
        try:
            data = ""

            if connection not in self.connections.keys():
                if connection is None:
                    connection = self.connections.keys()[0]
                else:
                    return "Connection not in connected devices"

            while True and self.status:

                data_part = self.find_correct_packet("DATA or FIN", connection)
                if not self.status:
                    print "I am disconnectiong cause sock is dead"
                    return "Disconnected"
                if data_part.packet_type() == "FIN":
                    self.disconnect(connection)
                    return "Disconnected"
                checksum_value = TCP.checksum(data_part.data)

                while checksum_value != data_part.checksum:

                    data_part = self.find_correct_packet("DATA or FIN", connection)
                    checksum_value = TCP.checksum(data_part.data)

                if data_part.data != "END":
                    data += data_part.data
                self.connections[connection].ack = data_part.seq + len(data_part.data)
                self.connections[connection].seq += 1  # syn flag is 1 byte
                self.connections[connection].set_flags(ack=True)
                packet_to_send = pickle.dumps(self.connections[connection])
                self.own_socket.sendto(packet_to_send, connection)  # after receiving correct info sends ack
                self.connections[connection].set_flags()

                if data_part.data == "END":
                    break

            return data
        except socket.error as error:
            print "Socket was closed before executing command. Error is: %s." % error
