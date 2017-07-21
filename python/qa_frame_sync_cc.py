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
    xcorr = np.correlate(x,pseq)#/np.sqrt(np.mean(np.abs(pseq)**2))
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
        pseq0_norm = pseq_list[0]/np.sqrt(np.sum(np.abs(pseq_list[0])**2))
        n_repeats = [3]
        x = np.zeros(N,dtype=np.complex128)
        for r in range(n_repeats[0]):
            x[toffset+r*zc_len:toffset+(r+1)*zc_len] = pseq0_norm
        hist_len = n_repeats[0]*pseq_list[0].size
        x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
        toffset_with_hist = toffset+hist_len

        vector_source = blocks.vector_source_c(x, True)
        head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
        frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.8)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,frame_sync)
        self.tb.connect(frame_sync,dst)

        self.tb.run ()
        in_data = dst.data()
        self.assertFloatTuplesAlmostEqual(in_data,x_with_history) # check the alignment is correct

        xcorr = frame_sync.get_crosscorr0(N)
        xcorr_with_history = np.append(np.zeros(hist_len-pseq0_norm.size+1,dtype=np.complex128), xcorr)#[pseq_list[0].size-1::]
        xcorr_true = cross_correlate(in_data,pseq0_norm)#in_data[hist_len::],pseq0_norm)
        # self.assertFloatTuplesAlmostEqual(xcorr[0:xcorr_true.size],xcorr_true,6)

        plt.plot(np.abs(xcorr_with_history))
        plt.plot(np.abs(xcorr_true),'r:')
        plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_cc, "qa_frame_sync_cc.xml")
