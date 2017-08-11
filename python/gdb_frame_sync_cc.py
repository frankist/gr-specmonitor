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

import os
import time
from gnuradio import gr
from gnuradio import blocks
import specmonitor as specmonitor
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt
import json

def cross_correlate(x,pseq):
    xcorr = np.correlate(x,pseq)#/np.sqrt(np.mean(np.abs(pseq)**2))
    return xcorr

def generate_preamble(zc_len, n_repeats):
    pseq_list = []
    pseq_norm_list = []
    for p in zc_len:
        pseq = zadoffchu.generate_sequence(p,1,0)
        pseq_list.append(pseq)
        pseq_norm = pseq / np.sqrt(np.sum(np.abs(pseq)**2))
        pseq_norm_list.append(pseq_norm)
    n_samples = np.sum([zc_len[i]*n_repeats[i] for i in range(len(zc_len))])
    x = np.zeros(n_samples,dtype=np.complex128)
    t = 0
    for i in range(len(zc_len)):
        for r in range(n_repeats[i]):
            x[t:t+zc_len[i]] = pseq_list[i]
            t = t + zc_len[i]

    return (x,pseq_list,pseq_norm_list)

class CreateRadio(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self,name="Frame Sync")
	N = 1000
	zc_len = [11,61]
	toffset = 100
	n_repeats = [3,1]
	samples_per_frame = N
	samples_of_awgn = 50
	preamble_amp = 1.0#np.random.uniform(0.5,100)
	awgn_floor = 1e-3
	precision_places = 5-int(round(np.log10(preamble_amp**2)))

	preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
	x = np.ones(N,dtype=np.complex128)*awgn_floor
	x[toffset:toffset+preamble.size] = preamble * preamble_amp
	hist_len = max(n_repeats[0]*pseq_list[0].size, zc_len[1]+2*5) # we have to account for margin
	x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
	toffset_with_hist = toffset+hist_len

	self.vector_source = blocks.vector_source_c(x, True)
	self.head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
	self.frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.8,samples_per_frame, samples_of_awgn)
	self.dst = blocks.vector_sink_c()

	self.connect(self.vector_source,self.head)
	self.connect(self.head,self.frame_sync)
	self.connect(self.frame_sync,self.dst)

    def test_run(self):
        start = time.time()
        self.run()
        end = time.time()
	print('Samples per sec [MHz]: ', 1000.0/1e6/(end-start))
	in_data = self.dst.data()
	print('Now HERE')
	# plt.plot(np.abs(in_data))
	# plt.show()

	###################### Visualization #######################
	# xcorr = frame_sync.get_crosscorr0(N)
	# xcorr_with_history = np.append(np.zeros(hist_len-zc_len[0]+1,dtype=np.complex128), xcorr)#[pseq_list[0].size-1::]
	# xcorr_true = cross_correlate(in_data,pseq_norm_list[0])#in_data[hist_len::],pseq0_norm)
	# self.assertFloatTuplesAlmostEqual(xcorr[0:xcorr_true.size],xcorr_true,6)

	# plt.plot(np.abs(in_data))
	# plt.plot(np.abs(xcorr_with_history))
	# plt.plot(np.abs(xcorr_true),'r:')
	# plt.show()

def main():
    """ go, go, go """
    top_block = CreateRadio()
    top_block.test_run()

if __name__ == "__main__":
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    raw_input ('Press Enter to continue: ')
    #for i in range(100000):
    main()

