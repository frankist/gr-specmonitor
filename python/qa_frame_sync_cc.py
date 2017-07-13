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

class qa_frame_sync_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        N = 1000
        zc_len = 11
        n_repeats = 4
        toffset = 100
        zc_seq = zadoffchu.generate_sequence(zc_len, 1, 0)
        x = np.zeros(N)
        for r in range(n_repeats):
            x[toffset+r*zc_len:toffset+(r+1)*zc_len] = zc_seq

        vector_source = blocks.vector_source_c(x, True)
        head = blocks.head(gr.sizeof_gr_complex, N)
        frame_sync = specmonitor.frame_sync_cc(zc_seq,n_repeats,0.8)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,frame_sync)
        # self.tb.connect(corr_est,tag_db)
        self.tb.connect(frame_sync,dst)

        self.tb.run ()
        in_data = dst.data()

        xcorr = frame_sync.get_crosscorr0(N)

        plt.plot(np.abs(xcorr))
        plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_cc, "qa_frame_sync_cc.xml")
