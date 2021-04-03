#!/usr/bin/env python3

import socket
import struct


class edppacket(object):
    def __init__(self, version, packet_type):
          # common header
          #  |Version|packet_type|length_common|checksum|
          #  |   B   |     B     |       B     |   H    |
          #  'B' ubyte format requires 0 <= number <= 255
          #  'H' format requires 0 <= number <= 65535
          #  'L' format requires 0 <= number <= 4294967295
          self.version = version
          self.packet_type = packet_type  # 0b001 for ACK, 0b010 for Control, 0b100 for data
          # self.src = src
          # self.dst = dst
          self.length_common = 9
          self.checksum = 0

          # ACK header
          #  |ack|wnd|flags|mMTU|
          #  | L | H |  B  |  H |
          self.ack = 0
          self.wnd = 0
          self.flags = 0
          self.mMTU = 0

          #Control header
          #  |ctr_length|ctr_mech| ... |ctr_mech|
          #  |     B    |    B   | ... |    B   |
          self.ctr_length = 0
          self.ctr_mech = []

          #Data header
          #  |seq#|data_length|Payload|
          #  | L  |     H     |       |
          self.seq = 0
          self.data_length = 0
          self.DAT = []  
          
          # self.Length = 0
          self.raw = b''


    def printrow(self):
      print(self.raw)
    # # Set header
    # def set_header(self, version, packet_type):
    #     self.version = version
    #     self.packet_type = packet_type
    #     if packet_type & 0b001:
    #       set_ack_header(ack, wnd, flags, mMTU)
    #     if packet_type & 0b010:
    #       set_ctr_header(ctr_length, ctr_mech)
    #     if packet_type & 0b100:
    #       set_data_header(seq, data_length, DAT)

    # Set ack_header
    def set_ack_header(self, ack, wnd, flags, mMTU):
        self.ack = ack
        self.wnd = wnd
        self.flags = flags
        self.mMTU = mMTU
        return 
    
    # set ctr_header
    def set_ctr_header(self, ctr_length, ctr_mech):
        self.ctr_length = ctr_length
        if ctr_length == 0:
          return
        self.ctr_mech = ctr_mech

    # set data_header
    def set_data_header(self, seq, data_length, DAT):
        self.seq = seq
        self.data_length = data_length
        self.DAT = DAT
          
    # Generate bytes of packet
    def packet2bytes(self):
          #Generate common header bytes format
          temp = struct.pack('!BBBH',
          self.version,
          #self.src,
          #self.dst,
          self.packet_type,
          self.length_common,
          self.checksum
          )
          self.raw = self.raw + temp

          # Generate ACK header
          if self.packet_type & 0b001 : # ACK packet
             temp = struct.pack('!LHBH',
             self.ack,
             self.wnd,
             self.flags,
             self.mMTU
             )
             self.raw = self.raw + temp

          # Generate Control header
          if self.packet_type & 0b010: #control packet
            self.raw = self.raw + struct.pack('!B', self.ctr_length) 
            for i in range(self.ctr_length):
              self.raw += struct.pack('!BB', self.ctr_mech[2*i], self.ctr_mech[2*i+1])
            
          # Generate DATA header
          if self.packet_type & 0b100:
             temp = struct.pack('!LH', self.seq, self.data_length)
             self.raw = self.raw + temp
             self.raw += self.DAT.encode()



    def bytes2packet(self, packet): 
          #given the string of bytes, recover the packet
          packet = packet[0:]
          # parse IP header
          # ip_header = packet[0:20]
          # iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
          # all the following values are incorrect
          # version_ihl = iph[0]
          # version = version_ihl >> 4
          # inh = version_ihl & 0xF
          # ttl = iph[5]
          # protocol = iph[6]
          # s_addr = socket.inet_ntoa(iph[8])
          # d_addr = socket.inet_ntoa(iph[9])

          # parse UDP header
          # udp_header = packet[20:28]
          # source_port, dest_port, data_length, checksum = struct.unpack("!HHHH",udp_header)

          # parse edp common header
          #packet = packet[28:]

          edp_common_header = packet[0:5]
          self.version, self.packet_type, self.length, self.checksum = struct.unpack("!BBBH", edp_common_header)
          packet = packet[5:]
          # parse the optional header
          if self.packet_type & 0b001:
            edp_ack_header = packet[0:9]
            self.ack, self.wnd, self.flags, self.mMTU = struct.unpack('!LHBH',edp_ack_header)
            packet = packet[9:]
          
          if self.packet_type & 0b010:
            # print(packet)
            # print(type(packet))
            # print(packet[0])
            self.ctr_length = packet[0]
            packet = packet[1:]
            for i in range(self.ctr_length):
              # temp1, temp2 = struct.unpack('!BB', packet[2*i:2*i+1])
              temp1 = packet[2*i]
              temp2 = packet[2*i+1]
              self.ctr_mech.append(temp1)
              self.ctr_mech.append(temp2)
            packet = packet[2*self.ctr_length:]

          if self.packet_type & 0b100:
            edp_data_header = packet[0:6]
            self.seq, self.data_length = struct.unpack('!LH',edp_data_header)
            packet = packet[6:]
            self.DAT = packet.decode()

    def generate_checksum(self):
        source_string = self.DAT
        # print(len(source_string))
        # print(source_string)
        my_sum = 0
        count_to = int((len(source_string) / 2)) * 2
        # print(count_to)
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
        self.checksum = answer
        #return answer



      

