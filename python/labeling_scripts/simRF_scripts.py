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

from gnuradio import gr
from gnuradio import channels
import sys
from bounding_box import *
import pkl_sig_format
import preamble_utils

class RF2FileFlowgraph:
    def __init__(self,xsource,linear_att,awgn_sigma,freq_offset,outputfile):
        self.tb = gr.top_block()

        self.source = blocks.vector_source_c(xsource,False)
        self.attenuation = blocks.multiply_const_cc(linear_att+0*1j)
        self.channel = channels.channel_model(awgn_sigma,freq_offset)
        self.fsink = blocks.file_sink_c(outputfile)

        self.tb.connect(self.source,self.attenuation)
        self.tb.connect(self.attenuation,self.channel)
        self.tb.connect(self.channel,self.fsink)

    def run(self):
        self.tb.run()

def file2frame_sync(sourcefilename,targetfilename,frame_params,n_sections):
    block_size = 1000

    while True:
        samples = pkl_sig_format.read_fc32_file(sourcefilename,i*block_size,block_size)
        if len(samples)==0:
            break
        pdetec.work(samples)

    if len(pdetec.peaks)>=n_sections:
        selected_peak_idxs = np.argsort([p.xcorr for p in pdetec.peaks])[-n_sections::]
        # TODO: check if they are at equivalent distances
        idx_sort = np.argsort([pdetec.peaks[i].tidx for i in selected_peak_idxs])
        peaks_selected = [pdetec.peaks[selected_peak_idxs[i]] for i in idx_sort]
        return (peaks_selected[0].tidx,peaks_selected)

    return None

# class File2FrameSyncFlowgraph:
#     def __init__(self,sourcefilename,targetfilename,frame_params):
#         self.tb = gr.top_block()

#         self.source = blocks.file_source_c(sourcefilename,False)
#         self.dst = blocks.vector_source_c()

#         self.tb.connect(self.source,self.framesync)
#         self.tb.connect(self.framesync,self.dst)

#     def run(self):
#         # run
#         selt.tb.run()


#         # if correct, save the sections into one file? This is fine. The spectrogram generator or final file cleaner

def run_RF_channel(args):
    params = args['parameters']
    targetfolder = args['targetfolder']
    sourcefilename = args['sourcefilename']
    tmp_file = targetfolder + '/tmp.bin'

    ### Read Signal already Framed and apply channel effects and settle time and writes to a temp file
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    prev_params = freader.parameters()
    num_samples_settle = args['settle_time'] * freader['parameters']['waveform']['sample_rate']
    tot_linear_gain = 10**((args['tx_gaindB']+args['rx_gaindB']-args['PLdB'])/20.0)
    noise_voltage = 10**((args['awgndBm']-30)/20.0)
    freq_offset = args.get('channel_frequency_offset',0)

    x = freader.read_section()
    x_with_settle = np.append(np.zeros(num_samples_settle,np.complex64),x)
    x_with_settle = np.append(x_with_settle,np.zeros(num_samples_settle/2,np.complex64)) # padding at the end

    # keep running until we get a successful preamble sync
    while True:
        rf_flowgraph = RF2FileFlowgraph(x_with_settle,tot_linear_gain,noise_voltage,freq_offset,tmp_file)
        rf_flowgraph.run() # this will stop after a while

        ### Read the temporary file, syncs, and writes the pickle
        ret = file2frame_sync(tmp_file,targetfilename,frame_params,n_sections)
        if ret is not None:
            # write file and discard padding samples
            break
        print 'Preamble sync has failed. Going to repeat transmission'


    # Note: The separation into multiple subsections happens later
