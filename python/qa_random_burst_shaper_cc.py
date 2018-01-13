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
from gnuradio import digital
import specmonitor_swig as specmonitor
import numpy as np
import matplotlib.pyplot as plt
import time
from scipy import signal

class qa_random_burst_shaper_cc (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        Nsamples = 1000
        dist = 'poisson'
        postpad = 20
        prepad = 0
        min_val = 2
        max_val = 30
        params = (postpad,min_val,max_val)
        burst_len = 10
        x = np.array(np.arange(100),np.complex64)#np.ones(1000,np.complex64)
        xtuple = tuple([complex(i) for i in x])

        vector_source = blocks.vector_source_c(xtuple,True)
        tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,burst_len,"packet_len")
        shaper = specmonitor.random_burst_shaper_cc(dist,params,prepad,[0],"packet_len")
        # shaper = digital.burst_shaper_cc((1+0*1j,),prepad,prepad,False)
        head = blocks.head(gr.sizeof_gr_complex, Nsamples)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,tagger)
        self.tb.connect(tagger,shaper)
        self.tb.connect(shaper,head)
        self.tb.connect(head,dst)
        self.tb.start()
        while dst.nitems_read(0) < Nsamples:
            time.sleep(0.01)
        self.tb.stop()
        self.tb.wait()
        # self.tb.run()
        xout = np.array(dst.data(),np.complex64)
        xoutmag2 = np.abs(xout)**2

        self.assertTrue(np.array_equal(xout[0:prepad],np.zeros(prepad,np.complex64)))
        self.assertTrue(np.array_equal(xout[prepad:prepad+burst_len],x[0:burst_len]))

        l = []
        l2 = []
        i=0
        while i < len(xoutmag2):
            if xoutmag2[i]>0:
                i+=1
                continue
            j = i
            while j < xoutmag2.size and xoutmag2[j]==0:
                j+=1
            l.append((i,j))
            l2.append(j-i)
            i=j+1
        print 'list of gaps: ', l
        print 'list of gap lengths: ', l2
        l.pop(0)
        l.pop()
        l2.pop(0)
        l2.pop()
        self.assertTrue(np.all(np.array(l2)>=min_val))
        self.assertTrue(np.all(np.array(l2)<=max_val+1))

        # plt.plot(xoutmag2)
        # plt.show()

    def test_002_t (self):
        Nsamples = 10000
        dist = 'poisson'
        postpad = 400
        prepad = 0
        min_val = 10
        max_val = 1000
        params = (postpad,min_val,max_val)
        burst_len = 500
        freq_values = (-0.325,-0.125,0.125,0.325)
        x = np.array(np.arange(100),np.complex64)#np.ones(1000,np.complex64)
        xtuple = tuple([complex(i) for i in x])

        vector_source = blocks.vector_source_c(xtuple,True)
        tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,burst_len,"packet_len")
        shaper = specmonitor.random_burst_shaper_cc(dist,params,prepad,freq_values,"packet_len")
        # shaper = digital.burst_shaper_cc((1+0*1j,),prepad,prepad,False)
        head = blocks.head(gr.sizeof_gr_complex, Nsamples)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,tagger)
        self.tb.connect(tagger,shaper)
        self.tb.connect(shaper,head)
        self.tb.connect(head,dst)
        self.tb.run()
        xout = np.array(dst.data(),np.complex64)
        xoutmag2 = np.abs(xout)**2

        self.assertTrue(np.array_equal(xout[0:prepad],np.zeros(prepad,np.complex64)))
        # self.assertTrue(np.array_equal(xout[prepad:prepad+burst_len],x[0:burst_len]))

        fftsize=64
        _,_,Sxx=signal.spectrogram(xout,1.0,noverlap=0,nperseg=fftsize,return_onesided=False,detrend=False)
        plt.imshow(Sxx)
        plt.show()
        # plt.plot(xoutmag2)
        # plt.show()

if __name__ == '__main__':
    gr_unittest.run(qa_random_burst_shaper_cc, "qa_random_burst_shaper_cc.xml")
