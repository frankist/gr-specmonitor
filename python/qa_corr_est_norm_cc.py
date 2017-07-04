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
from gnuradio import digital
import matplotlib.pyplot as plt
import specmonitor_swig as specmonitor
import numpy as np

class qa_corr_est_norm_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        sample_rate = 1e6
        total_samples = 10000
        preamble_seq = np.array([1,1,-1,1])
        preamble_seq /= len(preamble_seq)

        vector_source = blocks.vector_source_c(preamble_seq*4, True)
        head = blocks.head(gr.sizeof_gr_complex, total_samples)
        corr_est = specmonitor.corr_est_norm_cc(preamble_seq, 1, 0)
        # tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,corr_est)
        # self.tb.connect(corr_est,tag_db)
        self.tb.connect(corr_est,dst)

        self.tb.run()
        # check data
        in_data = dst.data()

        # plt.plot(np.abs(in_data))
        # plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_corr_est_norm_cc, "qa_corr_est_norm_cc.xml")
