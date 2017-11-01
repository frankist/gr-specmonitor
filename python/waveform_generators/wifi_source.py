#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Francisco Paisana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import numpy as np
import sys
import os
sys.path.append(os.path.abspath('../labeling_modules'))
from bounding_box import *

sys.path.append(
    os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))
from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from wifi_phy_hier import wifi_phy_hier  # grc-generated hier_block
import foo
import ieee802_11
import pmt
import time
import pickle
import filedata_handling as fdh
import logging
import gr_qtgui_utils

def print_params(params):
    logging.debug('bastian_ieee802_11 starting')
    for k, v in params.iteritems():
        logging.debug('%s: %s (type=%s)', k, v, type(v))


class GrWifiFlowgraph(gr.top_block):#gr_qtgui_utils.QtTopBlock):
    encoding_labels = [
        "BPSK 1/2", "BPSK 3/4", "QPSK 1/2", "QPSK 3/4", "16QAM 1/2",
        "16QAM 3/4", "64QAM 2/3", "64QAM 3/4"
    ]

    def __init__(self,
                 n_written_samples,
                 encoding=0,
                 pdu_length=500,
                 interval_ms=0,#300.0,
                 linear_gain=1.0):
        super(GrWifiFlowgraph, self).__init__() # this makes the initiation of all the qt nonsense

        # params
        self.n_written_samples = int(n_written_samples)
        self.linear_gain = float(linear_gain)
        self.pdu_length = pdu_length  # size of the message passed to the WiFi [1,1500]
        self.interval_ms = interval_ms  # period of message passing
        assert isinstance(encoding, (int, str))
        self.encoding = encoding if isinstance(encoding,int) else GrWifiFlowgraph.encoding_labels.index(encoding)
        self.num_msg = 100000000

        # phy
        self.wifi_phy_hier = wifi_phy_hier(
            bandwidth=20e6,  # NOTE: used by the Rx only
            chan_est=0,  # NOTE: used by the Rx only
            encoding=self.encoding,
            frequency=5.89e9,  # NOTE: Rx only
            sensitivity= 0.56,  # NOTE: Rx only
        )
        self.foo_packet_pad2 = foo.packet_pad2(
            False, False, 0.01,
            100, # Before padding
            1000)  # After padding
        self.foo_packet_pad2.set_min_output_buffer(
            96000)  # CHECK: What does this do?
        # self.time_plot = gr_qtgui_utils.make_time_sink_c(1024, 20.0e6, "", 1)

        self.blocks_null_source = blocks.null_source(gr.sizeof_gr_complex * 1)
        self.head = blocks.head(gr.sizeof_gr_complex, self.n_written_samples)
        self.dst = blocks.vector_sink_c()
        # dst = blocks.file_sink(gr.sizeof_gr_complex,args['targetfolder']+'/tmp.bin')

        # mac
        self.ieee802_11_mac = ieee802_11.mac(
            ([0x23, 0x23, 0x23, 0x23, 0x23, 0x23]),
            ([0x42, 0x42, 0x42, 0x42, 0x42, 0x42]),
            ([0xff, 0xff, 0xff, 0xff, 0xff, 255]))
        pmt_message = pmt.intern("".join("x" for i in range(self.pdu_length)))
        # self.message_strobe = foo.periodic_msg_source(pmt_message,
        #                                               self.interval_ms, self.num_msg, True, False)
        self.message_strobe = blocks.message_strobe(
            pmt.intern("".join("x" for i in range(self.pdu_length))),
            self.interval_ms)  # NOTE: This sends a message periodically
        # self.message_debug = blocks.message_debug()

        self.setup_flowgraph()

    def setup_flowgraph(self):
        ##################################################
        # Connections
        ##################################################
        # self.msg_connect((self.blocks_message_strobe,'strobe'),(self.message_debug,'print'))
        self.msg_connect((self.message_strobe, 'strobe'),
                         (self.ieee802_11_mac, 'app in'))
        self.msg_connect((self.ieee802_11_mac, 'phy out'),
                         (self.wifi_phy_hier, 'mac_in'))
        self.msg_connect((self.wifi_phy_hier, 'mac_out'),
                         (self.ieee802_11_mac, 'phy in'))
        self.connect((self.blocks_null_source, 0),
                     (self.wifi_phy_hier, 0))  # no reception

        self.connect((self.wifi_phy_hier, 0), self.foo_packet_pad2)
        # self.connect((self.wifi_phy_hier, 0), self.time_plot)
        self.connect(self.foo_packet_pad2, self.head)
        self.connect(self.head, self.dst)

    def run(self): #NOTE: The message probe does not stop the block, so I had to find a work around
        self.start()
        # while self.message_strobe.is_running():
        #     time.sleep(0.01)
        while self.dst.nitems_read(0)<self.n_written_samples:
            time.sleep(0.01)
        self.stop()
        self.wait()

def run_wifi_source(args):
    d = args['parameters']
    # print_params(d)

    # create Wifi block
    tb = GrWifiFlowgraph(
        d['number_samples'],
        encoding=d['encoding'],
        pdu_length=d['pdu_length'],
        interval_ms=d['interval_ms'])

    logging.info('Starting GR waveform generator script for Wifi')
    tb.run()
    logging.debug('GR script finished')

    gen_data = np.array(tb.dst.data())
    # plt.plot(np.abs(gen_data))
    # plt.show()

    logging.info('Going to compute Bounding Boxes')
    box_list = compute_bounding_boxes(gen_data)
    logging.debug('Finished computing the Bounding Boxes')
    # print [(b.time_bounds,b.freq_bounds) for b in box_list]
    box_pwr_list = compute_boxes_pwr(gen_data, box_list)
    max_pwr_box = np.max(box_pwr_list)
    gen_data /= np.sqrt(max_pwr_box)

    logging.debug('Going to fill the stage data structure and save to file')
    v = fdh.init_metadata()
    v['IQsamples'] = gen_data
    fdh.set_stage_derived_parameter(v, args['stage_name'], 'bounding_boxes',
                                    box_list)
    fdh.set_stage_parameters(v, args['stage_name'], args['parameters'])
    fname = args['targetfilename']
    with open(fname, 'wb') as f:
        pickle.dump(v, f)
    logging.debug('Finished writing to file %s', fname)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    targetfile = '~/tmp/out.pkl'
    args = {
        'parameters': {
            'number_samples': 100000,
            'encoding': 0,
            'pdu_length': 500,
            'interval_ms': 0#1000
        },
        'targetfilename': targetfile,
        'stage_name': 'waveform'
    }
    run_wifi_source(args)
    import pkl_sig_format
    dat = WaveformPklReader(targetfile)
    x = dat.read_section()
    plt.plot(np.abs(x))
    plt.show()
    os.remove(targetfile)
