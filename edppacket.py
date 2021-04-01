#!/usr/bin/env python3

import socket
import struct


class edppacket:
    def __init__(self, version, packet_type):
          # common header
          #  |Version|packet_type|length|checksum|
          #  |  1B   |    1B     |  1B  |   2B   |
          self.version = 0
          self.packet_type = 0  # 0b001 for ACK, 0b010 for Control, 0b100 for data
          # self.src = src
          # self.dst = dst
          self.length_common = 9
          self.checksum = 0

          # ACK header
          #  |ack|wnd|flags|mMTU|
          #  |4B |2B | 1B  | 2B |
          self.ack = 0
          self.wnd = 0
          self.flags = 0
          self.mMTU = 0

          #Control header
          #  |ctr_length|ctr_mech| ... |ctr_mech|
          #  |    1B    |   1B   | ... |   1B   |
          self.ctr_length = 0
          self.ctr_mech = []

          #Data header
          #  |seq#|data_length|Payload|
          #  | 4B |     2B    |       |
          self.seq = 0
          self.data_length = 0
          self.DAT = 0  
          
          # self.Length = 0
          self.raw = None

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
        self.ack = struct.pack('!L', ack)
        self.wnd = struct.pack('!H',wnd)
        self.flags = struct.pack('!B',flags)
        self.mMTU = struct.pack('!H',mMTU)
        return 
    
    # set ctr_header
    def set_ctr_header(self, ctr_length, ctr_mech):
        self.ctr_length = struct.pack('!B', ctr_length)
        for i in range(ctr_length):
          self.ctr_mech = self.ctr_mech + struct.pack('!BB', ctr_mech[2*i], ctr_mech[2*i+1])

    # set data_header
    def set_data_header(self, seq, data_length, DAT):
        self.seq = struct.pack('!L', seq)
        self.data_length = struct.pack('!H', data_length)
        self.DAT = DAT.encode()
          
    # Generate bytes of packet
    def packet2bytes(self):
          #Generate common header bytes format
          temp = struct.pack('!BHHBBH',
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
             temp = struct.pack('!BHHBBH',
             self.ack,
             self.wnd,
             self.flags,
             self.mMTU
             )
             self.raw = self.raw + temp

          # Generate Control header
          if self.packet_type & 0b010: #control packet
             self.raw = self.raw + self.ctr_length + self.ctr_mech
            
          # Generate DATA header
          if self.packet_type & 0b100:
             self.raw = self.raw + self.seq + self.data_length +self.DAT



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
          packet = packet[28:]
          edp_common_header = packet[0:5]
          self.version, self.packet_type, self.length, self.checksum = struct.unpack("!BBBH", edp_common_header)
          packet = packet[5:]
          # parse the optional header
          if self.packet_type & 0b001:
            edp_ack_header = packet[0:9]
            self.ack, self.wnd, self.flags, self.mMTU = struct.unpack('!4sHBH',edp_ack_header)
            packet = packet[9:]
          
          if self.packet_type & 0b010:
            edp_control_header_1 = packet[0:1]
            self.ctr_length = struct.unpack('!B', edp_control_header_1)
            for i in range(self.ctr_length):
              edp_control_header_2_temp = packet[2*i+1, 2*i]
              self.ctr_mech += struct.unpack('!BB', edp_control_header_2_temp)
            packet = packet[2*self.ctr_length]

          if self.packet_type & 0b100:
            edp_data_header = packet[0:6]
            self.seq, self.data_length = struct.unpack('!4sH',edp_data_header)
            packet = packet[6]
            self.DAT = packet





      

