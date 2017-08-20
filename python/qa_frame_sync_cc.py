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

class qa_frame_sync_cc (gr_unittest.TestCase):
    def setUp (self):
        print "Starting test..."
        self.tb = gr.top_block ()

    def tearDown (self):
        print "Tearing Down..."
        self.tb = None
        print "done."

    # def test_001_t (self):
    #     # In this test, we check if *one* preamble is detected with the correct
    #     # amplitude, CFO zero, and at the correct timestamp
    #     N = 1000
    #     zc_len = [11,61]
    #     toffset = 100
    #     n_repeats = [3,1]
    #     samples_per_frame = 1000
    #     samples_of_awgn = 50
    #     preamble_amp = np.random.uniform(0.5,100)
    #     awgn_floor = 1e-3
    #     precision_places = 5-int(round(np.log10(preamble_amp**2)))

    #     preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
    #     x = np.ones(N,dtype=np.complex128)*awgn_floor
    #     x[toffset:toffset+preamble.size] = preamble * preamble_amp
    #     hist_len = max(n_repeats[0]*pseq_list[0].size, zc_len[1]+2*5) # we have to account for margin
    #     x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
    #     toffset_with_hist = toffset+hist_len

    #     vector_source = blocks.vector_source_c(x, True)
    #     head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
    #     frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.8,samples_per_frame, samples_of_awgn)
    #     dst = blocks.vector_sink_c()

    #     self.tb.connect(vector_source,head)
    #     self.tb.connect(head,frame_sync)
    #     self.tb.connect(frame_sync,dst)

    #     self.tb.run ()
    #     in_data = dst.data()
    #     h = frame_sync.history()-1
    #     self.assertEqual(h,hist_len)
    #     self.assertFloatTuplesAlmostEqual(in_data,x_with_history,5) # check the alignment is correct
    #     # plt.plot(np.abs(in_data))
    #     # plt.show()

    #     ####################### Unit Test ##########################
    #     # Check if the preamble starts at expected time
    #     range_test = np.array([-1,0,preamble.size-1]) + hist_len + toffset
    #     true_mag_values = np.sqrt(np.array([awgn_floor,preamble_amp,preamble_amp])**2)
    #     self.assertFloatTuplesAlmostEqual(np.abs([in_data[i] for i in range_test]),true_mag_values,precision_places)

    #     # Check if the peak was detected by the crosscorr_detector
    #     peak_js = frame_sync.get_crosscorr0_peaks()
    #     #print('Received the json string:',peak_js)
    #     js_dict = json.loads(peak_js)
    #     self.assertEqual(len(js_dict),1)
    #     self.assertAlmostEqual(js_dict[0]['idx'], toffset + hist_len + zc_len[0]*(n_repeats[0]-1))
    #     self.assertAlmostEqual(js_dict[0]['corr_val'], preamble_amp**2,precision_places)
    #     self.assertEqual(js_dict[0]['valid'], True)
    #     self.assertAlmostEqual(complex(js_dict[0]['schmidl_mean']),preamble_amp**2+0j,precision_places)
    #     self.assertEqual(len(js_dict[0]['schmidl_vals']),n_repeats[0]-1)

    #     # Check if the peak is being tracked by the crosscorr_tracker
    #     # If all went well, the tracker must have found the pseq1, and updated the peak_idx for the next frame
    #     tracked_peak_js = frame_sync.get_peaks_json()
    #     # print('Received the json string: ', tracked_peak_js)
    #     js_dict = json.loads(tracked_peak_js)
    #     self.assertEqual(js_dict[0]['peak_idx'], toffset + hist_len + samples_per_frame)
    #     self.assertAlmostEqual(js_dict[0]['peak_amp'], preamble_amp**2,precision_places)
    #     self.assertAlmostEqual(js_dict[0]['cfo'], 0.0)
    #     self.assertEqual(js_dict[0]['n_frames_elapsed'], 1)
    #     self.assertEqual(js_dict[0]['n_frames_detected'], 1)

    #     ###################### Visualization #######################
    #     # xcorr = frame_sync.get_crosscorr0(N)
    #     # xcorr_with_history = np.append(np.zeros(hist_len-zc_len[0]+1,dtype=np.complex128), xcorr)#[pseq_list[0].size-1::]
    #     # xcorr_true = cross_correlate(in_data,pseq_norm_list[0])#in_data[hist_len::],pseq0_norm)
    #     # self.assertFloatTuplesAlmostEqual(xcorr[0:xcorr_true.size],xcorr_true,6)

    #     # plt.plot(np.abs(in_data))
    #     # plt.plot(np.abs(xcorr_with_history))
    #     # plt.plot(np.abs(xcorr_true),'r:')
    #     # plt.show()

    # def test_001_t(self):
    #     N = 10500
    #     zc_len = [11,61]
    #     toffset = np.random.randint(0,1000)#100
    #     n_repeats = [3,1]
    #     samples_per_frame = 1000
    #     samples_of_awgn = 50
    #     preamble_amp = 1.5#np.random.uniform(0.5,100)
    #     awgn_floor = 1e-3
    #     cfo = 0.45/zc_len[0]
    #     precision_places = 5-int(round(np.log10(preamble_amp**2)))

    #     # derived
    #     preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
    #     x = np.ones(N,dtype=np.complex128)*awgn_floor
    #     x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
    #     hist_len = max(n_repeats[0]*pseq_list[0].size, zc_len[1]+2*5) # we have to account for margin
    #     x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
    #     toffset_with_hist = toffset+hist_len
    #     N_frames_tot = int(np.ceil((N-toffset-preamble.size)/float(samples_per_frame)))
    #     tpseq1 = toffset + zc_len[0]*n_repeats[0]
    #     preamble_awgn_crosscorr = np.abs(np.sum(apply_cfo(x[tpseq1:tpseq1+zc_len[1]],-cfo)*np.conj(pseq_norm_list[1])))**2/zc_len[1]
    #     preamble_awgn_mag2 = np.mean(np.abs(x[tpseq1:tpseq1+zc_len[1]])**2)

    #     vector_source = blocks.vector_source_c(x, True)
    #     head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
    #     frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.5,samples_per_frame, samples_of_awgn, awgn_floor**2)
    #     dst = blocks.vector_sink_c()

    #     self.tb.connect(vector_source,head)
    #     self.tb.connect(head,frame_sync)
    #     self.tb.connect(frame_sync,dst)

    #     print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #     print '\nTest: '
    #     print '- toffset: ', toffset
    #     print '- preamble start:', toffset+hist_len
    #     print ''

    #     self.tb.run ()
    #     in_data = dst.data()
    #     h = frame_sync.history()-1
    #     self.assertEqual(h,hist_len)
    #     self.assertFloatTuplesAlmostEqual(in_data,x_with_history,5) # check the alignment is correct
    #     print 'GR run completed\n'
    #     # raw_input ('Press Enter to continue: ')
    #     # plt.plot(np.abs(in_data))
    #     # plt.show()

    #     # Check if the preambles are being tracked by the crosscorr_tracker
    #     js_dict = json.loads(frame_sync.get_peaks_json())
    #     # print('Received the json string: ', tracked_peak_js)
    #     self.assertEqual(len(js_dict),1)
    #     self.assertEqual(js_dict[0]['peak_idx'], toffset + hist_len + samples_per_frame*N_frames_tot)
    #     self.assertAlmostEqual(js_dict[0]['peak_corr'], preamble_awgn_crosscorr,precision_places)
    #     self.assertAlmostEqual(js_dict[0]['peak_mag2'], preamble_awgn_mag2, precision_places)
    #     self.assertAlmostEqual(js_dict[0]['cfo'], cfo, compute_precision(cfo))
    #     self.assertAlmostEqual(js_dict[0]['awgn_estim'], awgn_floor**2, compute_precision(awgn_floor**2))
    #     self.assertEqual(js_dict[0]['n_frames_elapsed'], N_frames_tot)
    #     self.assertEqual(js_dict[0]['n_frames_detected'], N_frames_tot)

    def test_001_t(self):
        N = 9000#9000
        zc_len = [5,13]
        toffset = 3500#8070
        n_repeats = [500,1]
        samples_per_frame = 9000
        samples_of_awgn = 50
        preamble_amp = 1.5#np.random.uniform(0.5,100)
        awgn_floor = 1e-3
        cfo = 0#0.45/zc_len[0]

        for r in range(N-np.sum([n_repeats[i]*zc_len[i] for i in range(2)])):
            self.tb = gr.top_block ()
            toffset = r
            # derived
            preamble, pseq_list, pseq_norm_list = generate_preamble(zc_len,n_repeats)
            x = np.ones(N,dtype=np.complex128)*awgn_floor
            x = add_preambles(x,toffset,apply_cfo(preamble*preamble_amp, cfo),samples_per_frame)
            hist_len = 2*preamble.size + samples_of_awgn
            # hist_len = max(max(n_repeats[0]*pseq_list[0].size, zc_len[1]+2*5),samples_of_awgn) # we have to account for margin
            x_with_history = np.append(np.zeros(hist_len,dtype=np.complex128),x)
            toffset_with_hist = toffset+hist_len
            N_frames_tot = int(np.ceil((N-toffset-preamble.size)/float(samples_per_frame)))

            vector_source = blocks.vector_source_c(x, True)
            head = blocks.head(gr.sizeof_gr_complex, len(x_with_history))
            frame_sync = specmonitor.frame_sync_cc(pseq_list,n_repeats,0.5,samples_per_frame, samples_of_awgn, awgn_floor**2)
            dst = blocks.vector_sink_c()

            self.tb.connect(vector_source,head)
            self.tb.connect(head,frame_sync)
            self.tb.connect(frame_sync,dst)

            print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
            print '\nTest: '
            print '- toffset: ', toffset
            print '- preamble start:', toffset+hist_len
            print '- crosscorr peak0: ', toffset+hist_len+(n_repeats[0]-1)*zc_len[0]
            print '- preamble end: ', toffset+hist_len+n_repeats[0]*zc_len[0]+n_repeats[1]*zc_len[1]
            print '- number of preambles: ', N_frames_tot
            print ''

            self.tb.run ()
            in_data = dst.data()
            h = frame_sync.history()-1
            self.assertEqual(h,hist_len)
            self.assertFloatTuplesAlmostEqual(in_data,x_with_history,5) # check the alignment is correct
            # raw_input ('Press Enter to continue: ')
            # plt.plot(np.abs(in_data))
            # plt.show()

            js_dict = json.loads(frame_sync.get_crosscorr0_peaks())
            if len(js_dict)>1:
                xcorr = frame_sync.get_crosscorr0(1000)
                plt.plot(np.abs(xcorr))
                plt.show()
            self.assertEqual(len(js_dict),1)
            # Check if the preambles are being tracked by the crosscorr_tracker
            js_dict = json.loads(frame_sync.get_peaks_json())
            # print('Received the json string: ', tracked_peak_js)
            self.assertEqual(len(js_dict),1)
            self.assertEqual(js_dict[0]['peak_idx'], toffset + hist_len + samples_per_frame*N_frames_tot)
            # self.assertAlmostEqual(js_dict[0]['cfo'], cfo, 4)#compute_precision(cfo))
            self.assertAlmostEqual(js_dict[0]['awgn_estim'], awgn_floor**2, compute_precision(awgn_floor**2))
            self.assertEqual(js_dict[0]['n_frames_elapsed'], N_frames_tot)
            self.assertEqual(js_dict[0]['n_frames_detected'], N_frames_tot)

if __name__ == '__main__':
    gr_unittest.run(qa_frame_sync_cc, "qa_frame_sync_cc.xml")
