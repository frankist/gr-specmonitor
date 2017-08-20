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

from gnuradio import gr
from gnuradio import blocks
import specmonitor as specmonitor
import zadoffchu
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import time

def cross_correlate(x,pseq):
    xcorr = np.correlate(x,pseq)#/np.sqrt(np.mean(np.abs(pseq)**2))
    return xcorr

def apply_cfo(x,cfo):
    x_cfo = x * np.exp(1j*2*np.pi*cfo*np.arange(x.size))
    return x_cfo

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

def add_preambles(x,toffset,preamble,frame_dur):
    k = 0
    first_idx = toffset + k*frame_dur
    while first_idx <= x.size:
        preamble_size_copied = min(x.size-first_idx,preamble.size)
        x[first_idx:first_idx+preamble_size_copied] += preamble[0:preamble_size_copied]
        k+=1
        first_idx = toffset + k*frame_dur
    return x

def compute_precision(true_value):
    precision_places = 4-int(round(np.log10(max(float(true_value),1.0e-5))))
    return precision_places

def test():
    N = 9000#9000
    zc_len = [5,13]
    toffset = 3500#8070
    n_repeats = [500,1]
    samples_per_frame = 8000
    samples_of_awgn = 50
    preamble_amp = 1.5#np.random.uniform(0.5,100)
    awgn_floor = 1e-3
    cfo = 0.45/zc_len[0]

    for r in range(N-np.sum([n_repeats[i]*zc_len[i] for i in range(2)])):
        tb = gr.top_block()
        toffset = r
        # derived
        preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
        x = np.ones(N,dtype=np.complex128)*awgn_floor
        x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
        hist_len = preamble.size + samples_of_awgn
        # hist_len = max(max(n_repeats[0]*pseq_list[0].size, zc_len[1]+2*5),samples_of_awgn) # we have to account for margin
        x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
        toffset_with_hist = toffset+hist_len
        N_frames_tot = int(np.ceil((N-toffset-preamble.size)/float(samples_per_frame)))

        vector_source = blocks.vector_source_c(x, True)
        head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
        frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.5,samples_per_frame, samples_of_awgn, awgn_floor**2)
        dst = blocks.vector_sink_c()

        tb.connect(vector_source,head)
        tb.connect(head,frame_sync)
        tb.connect(frame_sync,dst)

        print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
        print '\nTest: '
        print '- toffset: ', toffset
        print '- preamble start:', toffset+hist_len
        print '- crosscorr peak0: ', toffset+hist_len+(n_repeats[0]-1)*zc_len[0]
        print '- preamble end: ', toffset+hist_len+n_repeats[0]*zc_len[0]+n_repeats[1]*zc_len[1]
        print '- number of preambles: ', N_frames_tot
        print ''

        tb.run ()
        in_data = dst.data()
        h = frame_sync.history()-1

if __name__ == '__main__':
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    raw_input ('Press Enter to continue: ')
    test()
