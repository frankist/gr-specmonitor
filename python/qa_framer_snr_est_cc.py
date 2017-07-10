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
from gnuradio import analog
import specmonitor_swig as specmonitor
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt

class qa_framer_snr_est_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        # We check if with a constant source, the SNR is measured correctly
        sample_rate = 1e6
        frame_duration = 1.0e-3
        test_duration = 1.5*frame_duration
        snr = np.random.rand()*1000
        zc_seq_len = 71

        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        snr_estim_sample_window = zc_seq_len#int(round(samples_per_frame/20))
        random_samples_skip = np.random.randint(samples_per_frame/2)+samples_per_frame/2
        preamble_seq = zadoffchu.generate_sequence(zc_seq_len,1,0)
        preamble_pwr_sum = np.sum(np.abs(preamble_seq)**2)

        print "***** Start test 001 *****"
        framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        const_source = blocks.vector_source_c([1.0/snr],True)
        add = blocks.add_cc()
        skiphead = blocks.skiphead(gr.sizeof_gr_complex, random_samples_skip)
        corr_est = specmonitor.corr_est_norm_cc(preamble_seq,1,0)#digital.corr_est_cc(preamble_seq, 1, 0)
        snr_est = specmonitor.framer_snr_est_cc(snr_estim_sample_window, preamble_seq.size)
        # tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        dst = blocks.vector_sink_c()

        self.tb.connect(framer,(add,0))
        self.tb.connect(const_source,(add,1))
        self.tb.connect(add,skiphead)
        self.tb.connect(skiphead,head)
        self.tb.connect(head,corr_est)
        self.tb.connect(corr_est,snr_est)
        # self.tb.connect(snr_est,tag_db)
        self.tb.connect(snr_est,dst)

        self.tb.run()
        x_data = dst.data()

        snrdB = snr_est.SNRdB()
        y_data = np.abs(x_data)**2

        # print "Random Initial Skip: ", random_samples_skip
        # print "y_data size: ", len(y_data)

        start_preamble_idx = samples_per_frame - random_samples_skip + preamble_seq.size
        sig_range = np.arange(start_preamble_idx,start_preamble_idx+preamble_seq.size)
        floor_range = np.arange(sig_range[-1]+1,sig_range[-1]+1+snr_estim_sample_window)
        y_pwr = np.mean(y_data[sig_range])
        floor_pwr = np.mean(y_data[floor_range])
        py_snrdB = 10*np.log10(y_pwr/floor_pwr)

        self.assertAlmostEqual(py_snrdB,20*np.log10(snr),1)
        self.assertAlmostEqual(snrdB,20*np.log10(snr),1)

        # plt.plot(10*np.log10(y_data))
        # plt.plot(sig_range,10*np.log10(y_data[sig_range]),'rx')
        # plt.plot(floor_range,10*np.log10(y_data[floor_range]),'gx')
        # plt.show()
        
    def test_002_t (self):
        # set up fg
        sample_rate = 1e6
        frame_duration = 1.0e-3
        test_duration = 2*frame_duration
        snr = 100
        zc_seq_len=71

        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        n_samples_snr_estim = zc_seq_len#samples_per_frame/20
        random_samples_skip = 0#np.random.randint(samples_per_frame)
        preamble_seq = zadoffchu.generate_sequence(zc_seq_len,1,0)
        preamble_pwr_sum = np.sum(np.abs(preamble_seq)**2)

        print "***** Start test 002 *****"
        framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        awgn = analog.noise_source_c(analog.GR_GAUSSIAN,1.0/snr)
        add = blocks.add_cc()
        corr_est = specmonitor.corr_est_norm_cc(preamble_seq,1,0)#digital.corr_est_cc(preamble_seq, 1, 0)
        snr_est = specmonitor.framer_snr_est_cc(n_samples_snr_estim, preamble_seq.size)
        tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        dst = blocks.vector_sink_c()

        self.tb.connect(framer,(add,0))
        self.tb.connect(awgn,(add,1))
        self.tb.connect(add,corr_est)
        self.tb.connect(corr_est,snr_est)
        self.tb.connect(snr_est,tag_db)
        self.tb.connect(snr_est,head)
        self.tb.connect(head,dst)

        self.tb.run ()
        x_data = dst.data()

        print "The final SNR is: ", snr_est.SNRdB()


        plt.plot(10*np.log10(np.abs(x_data)**2))
        plt.show()


if __name__ == '__main__':
    gr_unittest.run(qa_framer_snr_est_cc, "qa_framer_snr_est_cc.xml")
