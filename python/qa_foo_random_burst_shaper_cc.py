#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2018 <+YOU OR YOUR COMPANY+>.
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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import specmonitor_swig as specmonitor
import matplotlib.pyplot as plt
import time
import sys
import os
import numpy as np

sys.path.append(
    os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))
import foo
from wifi_phy_hier import wifi_phy_hier  # grc-generated hier_block
import ieee802_11
import pmt

class qa_foo_random_burst_shaper_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # params
        self.n_written_samples = 100000
        self.linear_gain = 1.0
        self.pdu_length = 750
        self.encoding = 0
        self.pad_interval = 5000
        # phy
        self.wifi_phy_hier = wifi_phy_hier(
            bandwidth=20e6,  # NOTE: used by the Rx only
            chan_est=0,  # NOTE: used by the Rx only
            encoding=self.encoding,
            frequency=5.89e9,  # NOTE: Rx only
            sensitivity= 0.56,  # NOTE: Rx only
        )
        # self.packet_pad = foo.packet_pad2(
        #     False, # Debug
        #     False, 0.01,
        #     100, # Before padding
        #     self.pad_interval)  # After padding
        self.packet_pad = specmonitor.foo_random_burst_shaper_cc(
            False,
            False,
            0,
            'uniform',
            [0,self.pad_interval],
            100, [0])
        self.packet_pad.set_min_output_buffer(
            96000)
        self.blocks_null_source = blocks.null_source(gr.sizeof_gr_complex * 1)
        self.head = blocks.head(gr.sizeof_gr_complex, self.n_written_samples)
        self.dst = blocks.vector_sink_c()

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
            0)  # NOTE: This sends a message periodically

        # setup
        self.tb.msg_connect((self.message_strobe, 'strobe'),
                         (self.ieee802_11_mac, 'app in'))
        self.tb.msg_connect((self.ieee802_11_mac, 'phy out'),
                         (self.wifi_phy_hier, 'mac_in'))
        self.tb.msg_connect((self.wifi_phy_hier, 'mac_out'),
                         (self.ieee802_11_mac, 'phy in'))
        self.tb.connect((self.blocks_null_source, 0),
                     (self.wifi_phy_hier, 0))  # no reception
        self.tb.connect((self.wifi_phy_hier, 0), self.packet_pad)#self.foo_packet_pad2)
        self.tb.connect(self.packet_pad,self.head)
        # self.connect(self.foo_packet_pad2, self.head)
        self.tb.connect(self.head, self.dst)

        # run
        self.tb.start()
        # while self.message_strobe.is_running():
        #     time.sleep(0.01)
        while self.dst.nitems_read(0)<self.n_written_samples:
            time.sleep(0.01)
        self.tb.stop()
        self.tb.wait()

        # check data
        xout = np.abs(self.dst.data())
        self.assertAlmostEqual(np.max(xout[0:100]),0)
        # plt.plot(xout)
        # plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_foo_random_burst_shaper_cc, "qa_foo_random_burst_shaper_cc.xml")
