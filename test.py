#!usr/bin/env python3

from src.edppacket import *
import socket
import struct
import pickle

ack = 1
wnd = 2
flags = 3
mMTU = 4
ctr_length = 2
ctr_mech = [1,2,3,4]
seq = 5
data_length = 5
DAT = 'ABCDE'
00
edp_packet = edppacket(1,7)
if edp_packet.packet_type & 0b001:
    edp_packet.set_ack_header(ack, wnd, flags, mMTU)
if edp_packet.packet_type & 0b010:
    edp_packet.set_ctr_header(ctr_length, ctr_mech)
if edp_packet.packet_type & 0b100:
    edp_packet.set_data_header(seq, data_length, DAT)


edp_packet.packet2bytes()
print(edp_packet.raw)
edp_packet.bytes2packet(edp_packet.raw)
print(edp_packet.seq)
print(edp_packet.data_length)
print(edp_packet.mMTU)
print(edp_packet.DAT)
