#!/usr/bin/env python

import numpy as np
from gnuradio import gr
import pmt
import time
import socket
import struct
import pickle

# TCPClient Utils
def connect_client(addr=('127.0.0.1',9999)):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(addr)
    return clientsocket

def send_message(clientsocket,msg):
    msglen = len(msg)
    buf = struct.pack('h',msglen)+msg
    clientsocket.sendall(buf)

class darkflow_tcp_client(gr.basic_block):
    """
    This block passes an image to a TCP socket for remote processing
    """
    def __init__(self,yaml_cfg_file,addr=('127.0.0.1',9999),radio_metadata={}):
        # params
        self.yaml_file = yaml_cfg_file

        # setup gnuradio variables
        gr.basic_block.__init__(self,
            name="darkflow_tcp_client",
            in_sig=None,
            out_sig=None)
        self.message_port_register_in(pmt.intern("gray_img"))
        self.set_msg_handler(pmt.intern("gray_img"), self.tcp_send)

        # parse yaml configuration file
        self.ncols = radio_metadata['ncols']
        self.nrows = radio_metadata['nrows']

        # setup connection
        self.soc = connect_client(addr)

        # send metadata
        buf = struct.pack('h',0) + pickle.dumps(radio_metadata)
        send_message(self.soc,buf)
        self.counter_img = 0

    def tcp_send(self, msg):
        # convert message to numpy array
        u8img = pmt.pmt_to_python.uvector_to_numpy(msg).reshape(self.nrows,self.ncols)
        buf = struct.pack('h',1)+u8img.tostring()
        send_message(self.soc,buf)
        self.counter_img += 1
