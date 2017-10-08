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

class File2FrameSyncFlowgraph:
    def __init__(self,sourcefilename,targetfilename,frame_params):
        self.tb = gr.top_block()

        self.source = blocks.file_source_c(sourcefilename,False)
        self.framesync = specmonitor.frame_sync_cc(blablabla)
        self.dst = blocks.vector_source_c()

        self.tb.connect(self.source,self.framesync)
        self.tb.connect(self.framesync,self.dst)

    def run(self):
        self.tb.run()

        # check how many preambles were detected. If enough, we are fine. We can write the pickle
        pass

    def run(self):
        # run

        # check if you got the expected number of subsections

        # if correct, save the sections into one file? This is fine. The spectrogram generator or final file cleaner
        # will separate them later
        pass

def run_RF_channel(args):
    params = args['parameters']
    targetfolder = args['targetfolder']
    sourcefilename = args['sourcefilename']
    tmp_file = targetfolder + '/tmp.bin'

    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    prev_params = freader.parameters()
    num_samples_settle = args['settle_time'] * freader['parameters']['waveform']['sample_rate']
    tot_linear_gain = 10**((args['tx_gaindB']+args['rx_gaindB']-args['PLdB'])/20.0)
    noise_voltage = 10**((args['awgndBm']-30)/20.0)
    freq_offset = args.get('channel_frequency_offset',0)

    x = freader.read_section()
    x_with_settle = np.append(np.zeros(num_samples_settle,np.complex64),x)
    x_with_settle = np.append(x_with_settle,np.zeros(num_samples_settle/2,np.complex64)) # padding at the end

    rf_flowgraph = RF2FileFlowgraph(x_with_settle,tot_linear_gain,noise_voltage,freq_offset,tmp_file)

    rf_flowgraph.run() # this will stop after a while

    sync_flowgraph = File2FrameSyncFlowgraph(tmp_file,targetfilename,frame_params)

    sync_flowgraph.run() # this will stop after the file ends.
