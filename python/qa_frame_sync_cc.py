#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2017 <+YOU OR YOUR COMPANY+>.
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
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt

def cross_correlate(x,pseq):
    xcorr = np.correlate(x,pseq)/np.sqrt(np.mean(np.abs(pseq)**2))
    return xcorr

class qa_frame_sync_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        N = 1000
        zc_len = 11
        toffset = 100
        pseq_list = []
        pseq_list.append(zadoffchu.generate_sequence(zc_len, 1, 0))
        n_repeats = [4]
        x = np.zeros(N,dtype=np.complex128)
        for r in range(n_repeats[0]):
            x[toffset+r*zc_len:toffset+(r+1)*zc_len] = pseq_list[0]

        vector_source = blocks.vector_source_c(x, True)
        head = blocks.head(gr.sizeof_gr_complex, N)
        frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.8)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,frame_sync)
        # self.tb.connect(corr_est,tag_db)
        self.tb.connect(frame_sync,dst)

        self.tb.run ()
        in_data = dst.data()

        xcorr = frame_sync.get_crosscorr0(N)
        xcorr_true = cross_correlate(in_data,pseq_list[0])

        plt.plot(np.abs(xcorr))
        plt.plot(np.abs(xcorr_true),'r--')
        plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_cc, "qa_frame_sync_cc.xml")
