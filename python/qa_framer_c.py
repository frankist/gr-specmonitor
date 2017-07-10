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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from gnuradio import digital
from gnuradio import qtgui
from gnuradio import analog
import specmonitor_swig as specmonitor
import numpy as np
import matplotlib.pyplot as plt
import time

def zadoffchu(zc_length, u, q, n_start = 0, num_samples = -1):
    if num_samples < 0:
        num_samples = zc_length
    n_end = n_start + num_samples

    zc = [0]*num_samples#np.zeros(num_samples, dtype='complex')
    zc[0:num_samples] = [np.exp(np.complex(0,-1.0*np.pi*u*float(n*(n+1+2*q))/zc_length)) for n in range(n_start,n_end)]

    return zc

def barker(barker_length=13):
    b = [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]
    return [complex(i) for i in b]

class qa_framer_c(gr_unittest.TestCase):

    def setUp(self):
        self.tb = gr.top_block ()

    def tearDown(self):
        self.tb = None

    def test_001_t(self):
        # Generate empty frames with zadoff-chu sequence as preamble
        print "***** Start test 002 *****"
        sample_rate = 10.0e6
        frame_duration = 1.0e-3
        test_duration = frame_duration*100
        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        preamble_seq = zadoffchu(63,1,0)
        empty_frame = np.zeros(samples_per_test, dtype='complex')

        print 'This is a TEST with an empty frame'
        print 'Input variables: sample_rate: ', sample_rate, ' frame_duration: ', frame_duration
        print 'Derived variables: samples_per_frame: ', samples_per_frame, ' samples_per_test: ', samples_per_test
        t = 0
        while t < empty_frame.size:
            end_t = min((t+len(preamble_seq)), empty_frame.size)
            empty_frame[t:end_t] = preamble_seq[0:end_t-t]
            t = t + samples_per_frame

        framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        dst = blocks.vector_sink_c()
        self.tb.connect(framer,head)
        self.tb.connect(head,dst)

        t1 = time.time()
        self.tb.run()
        t2 = time.time()
        result_data = dst.data()
        print "Block Run Speed [MS/s]: ", samples_per_test/(t2-t1)/1.0e6
        # plt.plot(np.abs(result_data),'gx-')
        # plt.plot(np.abs(empty_frame),'r.-')
        # plt.show()
        self.assertEqual(empty_frame.size, samples_per_test)
        self.assertEqual(len(result_data), samples_per_test)
        self.assertFloatTuplesAlmostEqual(empty_frame, result_data, 6)

    def test_002_t(self):
        # Generate frames with AWGN and test SNR estimation
        sample_rate = 10.0e6
        frame_duration = 1.0e-3
        test_duration = 0.1*frame_duration
        snr = 10
        scale_value = 15.0
        samples_per_frame = int(round(frame_duration*sample_rate))
        samples_per_test = int(round(test_duration*sample_rate))
        random_samples_skip = 0#np.random.randint(samples_per_frame)
        preamble_seq = zadoffchu(63,1,0)
        preamble_pwr_sum = np.sum(np.abs(preamble_seq)**2)

        print "***** Start test 002 *****"
        framer = specmonitor.framer_c(sample_rate, frame_duration, preamble_seq)
        awgn = analog.noise_source_c(analog.GR_GAUSSIAN,1.0/snr)
        add = blocks.add_cc()
        scaler = blocks.multiply_const_vcc([complex(scale_value)])
        mag2 = blocks.complex_to_mag_squared()
        mavg = blocks.moving_average_ff(len(preamble_seq),1.0/len(preamble_seq))# i need to divide by the preamble size in case the preamble seq has amplitude 1 (sum of power is len)
        sqrtavg = blocks.transcendental("sqrt")

        # I have to compensate the amplitude of the input signal (scale) either through a feedback normalization loop that computes the scale, or manually (not practical)
        # additionally I have to scale down by the len(preamble)==sum(abs(preamble)^2) because the cross-corr does not divide by the preamble length
        #scaler2 = blocks.multiply_const_vcc([complex(1.0)/scale_value/len(preamble_seq)]) # if no feedback normalization loop, I have to scale the signal compensating additionally the scaling factor
        corr_est = specmonitor.corr_est_norm_cc(preamble_seq,1,0)#digital.corr_est_cc(preamble_seq, 1, 0)
        tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        head = blocks.head(gr.sizeof_gr_complex, samples_per_test)
        dst = blocks.vector_sink_c()

        skiphead = blocks.skiphead(gr.sizeof_float, random_samples_skip)
        skiphead2 = blocks.skiphead(gr.sizeof_gr_complex, random_samples_skip)
        skiphead3 = blocks.skiphead(gr.sizeof_gr_complex, random_samples_skip)
        debug_vec = blocks.vector_sink_f()
        debug_vec2 = blocks.vector_sink_c()
        debug_vec3 = blocks.vector_sink_c()

        self.tb.connect(framer,(add,0))
        self.tb.connect(awgn,(add,1))
        self.tb.connect(add,scaler)
        self.tb.connect(scaler,mag2,mavg,sqrtavg)

        self.tb.connect(scaler,corr_est)
        self.tb.connect(corr_est,tag_db)
        self.tb.connect(corr_est,head,dst)

        self.tb.connect(sqrtavg,skiphead,debug_vec)
        self.tb.connect(scaler,skiphead2,debug_vec2)

        self.tb.run()
        result_data = dst.data()
        debug_vec_data = debug_vec.data()
        debug_vec_data2 = debug_vec2.data()
        debug_vec_data3 = debug_vec3.data()


        # plt.plot(debug_vec_data)
        # plt.plot(np.abs(debug_vec_data2),'g')
        # plt.plot(np.abs(debug_vec_data3),'r')
        # plt.show()

        #plt.plot(np.abs(result_data))
        #plt.show()

        # corr_data = np.correlate(result_data, preamble_seq)
        # plt.plot(np.abs(corr_data))
        # plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_framer_c, "qa_framer_c.xml")
    pass
