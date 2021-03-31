#!/usr/bin/python
import socket
import struct


class edppacket:
    def __init__(self,version,connection_type, checksum=0, ack=0, seq = 0, win = 0, control = {'1':0,'2':0,'3':0}):
          self.version = version
          self.type = connection_type #1 for control, 2 for ack...
          self.DAT = data
          self.ack = ack
          self.seq = seq
          self.win = win
          self.checksum = checksum
          self.control ={}
          self.Length = 0
          self.raw = None

    def packet2bytes(self):
      #given the type of the packet, output the bytes format
          if self.type == 0x001: #control packet
             self.length = 
             self.raw = struct.pack('!BBBBBLLLL',
             self.version, 
             self.length,
             self.FIN ,
             self.DAT ,
             self.ACK ,
             self.Sequence, 
             self.Acknowledgement, 
             self.Window ,
             self.Length ,
             )

    def bytes2packet(buffer):

