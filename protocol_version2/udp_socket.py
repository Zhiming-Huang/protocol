
import threading
import time
import socket

PACKET_RETRANSMIT_MAX_COUNT = 3 # If data is not acked, the maxi time to resend
PACKET_RETRANSMIT_TIMEOUT = 1000 # Time to retransmit a packet if ACK not received
TIME_INTERVAL = 0.1

class udp_socket(object):
    def __init__(self, local_ip_address=None, local_port=None, remote_ip_address=None, remote_port=None):
        self.local_ip_address = None
        self.local_port = None
        self.remote_ip_address = None
        self.remote_port = None
        self.udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    def socket_id(self):
        return f"UDP/{self.local_ip_address}/{self.local_port}/{self.remote_ip_address}/{self.remote_port}"

    def bind(self):
        if self.local_ip_address!=None and self.local_port != None:
            self.udpsocket.bind((self.local_ip_address,self.local_port))

    def send_to(self, packet):
        self.udpsocket.sendto(packet, (self.remote_ip_address,self.remote_port))

    def receive_from(self, timeout=None):
        content, destInfo = self.udpsocket.recvfrom(1024)
        destInfo = destInfo
        return content

    def close(self):
        """ Close socket """
        self.udpsocket.close()
