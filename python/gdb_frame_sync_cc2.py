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
    n_repeats = [40,1]
    samples_per_frame = 9000
    samples_of_awgn = 50
    preamble_amp = np.random.uniform(0.5,100)
    awgn_floor = 1e-3

    for r in range(N-np.sum([n_repeats[i]*zc_len[i] for i in range(2)])):
        cfo = np.random.uniform(0,0.45)/zc_len[0]
        
        tb = gr.top_block()
        toffset = r
        # derived
        preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
        x = np.ones(N,dtype=np.complex128)*awgn_floor
        x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
        hist_len = 2*preamble.size + samples_of_awgn
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

        if(h != hist_len):
            print 'The history length is not consistent. ', h, '!=', hist_len
            return

        error_num = [False]*6
        js_dict0 = json.loads(frame_sync.get_crosscorr0_peaks())
        js_dict = json.loads(frame_sync.get_peaks_json())
        error_num[0] = False if len(js_dict0) == 1 else True
        error_num[1] = False if len(js_dict) == 1 else True
        if error_num[1] == False:
            error_num[2] = False if js_dict[0]['peak_idx']==(toffset+samples_per_frame*N_frames_tot) else True
            error_num[3] = False if js_dict[0]['n_frames_elapsed']==N_frames_tot else True
            error_num[4] = False if abs(js_dict[0]['awgn_estim']-awgn_floor**2)<0.001 else True
            error_num[5] = False if abs(js_dict[0]['cfo']-cfo)<0.001 else True
        if any(error_num):
            print 'There were errors', error_num
            xcorr = frame_sync.get_crosscorr0(1000)
            plt.plot(np.abs(xcorr))
            plt.show()
            return

def test_robustness_AWGN():
    N = 10000#9000
    zc_len = [29,201]
    n_repeats = [20,1]
    samples_per_frame = 2000
    samples_of_awgn = 50
    preamble_amp = np.random.uniform(0.5,100)
    SNRdBrange = range(-10,10)
    toffset = 200
    Nruns = 100
    sum_ratios = np.zeros(len(SNRdBrange))
    sum_falarm = np.zeros(len(SNRdBrange))

    cfo = 0#0.01
    for ii, s in enumerate(SNRdBrange):
        for rr in range(Nruns):
            awgn_pwr = preamble_amp**2/(10**(s/10.0))

            tb = gr.top_block()
            # derived
            preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
            x = np.random.normal(0, np.sqrt(awgn_pwr)/np.sqrt(2), N)+np.random.normal(0, np.sqrt(awgn_pwr)/np.sqrt(2), N)*1j
            x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
            hist_len = 2*preamble.size + samples_of_awgn
            x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
            toffset_with_hist = toffset+hist_len
            N_frames_tot = int(np.floor((N-toffset-preamble.size)/float(samples_per_frame))+1)

            vector_source = blocks.vector_source_c(x, True)
            head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
            frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.15,samples_per_frame, samples_of_awgn, awgn_pwr)
            dst = blocks.vector_sink_c()

            tb.connect(vector_source,head)
            tb.connect(head,frame_sync)
            tb.connect(frame_sync,dst)

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
            assert h == hist_len
            # raw_input ('Press Enter to continue: ')

            js_dict = json.loads(frame_sync.get_peaks_json())
            print js_dict
            if len(js_dict)>=1:
                n_frames_detected = js_dict[0]['n_frames_detected']
                print 'got:', js_dict[0]['peak_idx'], ', expected ', toffset+samples_per_frame*(N_frames_tot+1)
                if js_dict[0]['peak_idx']==(toffset+samples_per_frame*(N_frames_tot+1)):
                    r = n_frames_detected / float(N_frames_tot+1)
                    print 'r:', r
                    sum_ratios[ii] = sum_ratios[ii] + r
            sum_falarm[ii] += len(js_dict)-1

    rate_detection = sum_ratios / Nruns
    rate_falarm = sum_falarm / Nruns
    fig, (ax0, ax1) = plt.subplots(nrows=2)
    ax0.plot(SNRdBrange, rate_detection)
    ax1.plot(SNRdBrange, rate_falarm, ':')
    plt.show()

def check_speed():
    N = 100000#9000
    zc_len = [5,201]#[51,201]
    n_repeats = [20,1]#[10,1]
    samples_per_frame = 2000
    samples_of_awgn = 50
    preamble_amp = np.random.uniform(0.5,100)
    SNRdB = 10#range(-10,10)
    toffset = 200
    Nruns = 1
    thres = 0.7#0.15

    cfo = 0#0.01
    for rr in range(Nruns):
        awgn_pwr = preamble_amp**2/(10**(SNRdB/10.0))

        tb = gr.top_block()
        # derived
        preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
        x = np.random.normal(0, np.sqrt(awgn_pwr)/np.sqrt(2), N)+np.random.normal(0, np.sqrt(awgn_pwr)/np.sqrt(2), N)*1j
        x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
        hist_len = 2*preamble.size + samples_of_awgn
        x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
        toffset_with_hist = toffset+hist_len
        N_frames_tot = int(np.floor((N-toffset-preamble.size)/float(samples_per_frame))+1)

        vector_source = blocks.vector_source_c(x, True)
        head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
        frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,thres,samples_per_frame, samples_of_awgn, awgn_pwr)
        dst = blocks.vector_sink_c()

        tb.connect(vector_source,head)
        tb.connect(head,frame_sync)
        tb.connect(frame_sync,dst)

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
        assert h == hist_len
    # Benchmark results so far:
    # for [59,201] and n_repeats=[10,1]
    # With crosscorr detector work function runs at 11 MS/s
    # Without crosscorr detector work function runs at 11 MS/s
    # Inside crosscorr detector work function:
    # # 3 parts: volk section part, for loop, and after for loop. distribution of time: [0.85,0.15,0]
    # # # Inside volk section, the filter takes 0.8 of the section
    # # # Inside for loop, the if block takes 0.2 of the whole for loop



if __name__ == '__main__':
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    raw_input ('Press Enter to continue: ')
    # test_robustness_AWGN()
    check_speed()
    print 'Finished the simulation'
