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
from gnuradio import blocks
from gnuradio import channels
import sys
import os
from bounding_box import *
import pkl_sig_format
import preamble_utils
import filedata_handling as filedata
import pickle
import RF_sync_utils

# assert that the parameters provided are valid and read them
def read_and_assert_channel_amplitudes(stage_params):
    config_params = ['tx_gaindB','rx_gaindB','PLdB','awgndBm']
    def contains_any(any_of_these,container):
        return any([s in container for s in any_of_these])

    if 'SNRdB' in stage_params:
        if any([p in stage_params for p in config_params]):
            print 'ERROR: You either define the SNRdB of the channel or the hardware gains and pathloss'
            exit(-1)
        noise_voltage = 1.0
        tot_linear_gain = 10**(stage_params['SNRdB']/20.0)
    elif all([p in stage_params for p in config_params]):
        noise_voltage = 10**((stage_params['awgndBm']-30)/20.0)
        tot_linear_gain = 10**((stage_params['tx_gaindB']+stage_params['rx_gaindB']-stage_params['PLdB'])/20.0)
    else:
        print 'ERROR: You didn\'t specify the required parameters for the channel'
        exit(-1)

    return (tot_linear_gain,noise_voltage)

# read raw samples file and sync with the preambles
def emulate_repeating_RF_channel(outputfile,framed_signal,fparams,n_sections,Nsuperframe,params,Nsettle):
    ### Set variables based on given parameters
    tot_linear_gain,noise_voltage = read_and_assert_channel_amplitudes(params)
    freq_offset = params.get('channel_frequency_offset',0)
    DC_offset = params.get('DC_offset',0)
    DC_offset *= np.exp(1j*2*np.pi*np.random.rand(1)) # add a random phase
    DC_offset = DC_offset[0]
    # TODO: Understand why you get a list here

    print 'final SNRdB:', 10*np.log10(tot_linear_gain**2/noise_voltage**2)

    # get needed global parameters
    frame_period = fparams.frame_period

    ### Read Signal already Framed and apply channel effects, keep repeating, and writes the result to a temp file
    # GNURadio Flowgraph
    tb = gr.top_block()
    random_TxRx_unsync = np.random.randint(1000)
    Rx_num_samples = Nsuperframe+Nsettle # the settle is important both for the HW and pdetec history
    Rx_num_samples += frame_period + 10 # we will only choose peaks whose frame is whole. I just add an guard interval of a few samples

    source = blocks.vector_source_c(framed_signal,True) # keep repeating
    attenuation = blocks.multiply_const_cc(tot_linear_gain+0*1j)
    channel = channels.channel_model(noise_voltage,freq_offset)
    dc_block = blocks.add_const_cc(DC_offset+0*1j)
    skip = blocks.skiphead(gr.sizeof_gr_complex,random_TxRx_unsync)
    head = blocks.head(gr.sizeof_gr_complex,Rx_num_samples)
    fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

    tb.connect(source,attenuation)
    tb.connect(attenuation,channel)
    tb.connect(channel,dc_block)
    tb.connect(dc_block,skip)
    tb.connect(skip,head)
    tb.connect(head,fsink)

    tb.run()

class RF2FileFlowgraph:
    def __init__(self,xsource,linear_att,awgn_sigma,freq_offset,outputfile):
        self.tb = gr.top_block()

        print 'final SNRdB:', 10*np.log10(linear_att**2/awgn_sigma**2)

        v = np.array(xsource,np.complex128)
        self.source = blocks.vector_source_c(v,False)
        self.attenuation = blocks.multiply_const_cc(linear_att+0*1j)
        self.channel = channels.channel_model(awgn_sigma,freq_offset)
        self.fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

        self.tb.connect(self.source,self.attenuation)
        self.tb.connect(self.attenuation,self.channel)
        self.tb.connect(self.channel,self.fsink)

    def run(self):
        self.tb.run()

def run_RF_channel(args):
    params = args['parameters']
    targetfolder = args['targetfolder']
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']
    tmp_file = targetfolder + '/tmp.bin'

    ### Read previous stage data and sets the parameters of the new stage
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    filedata.set_stage_parameters(stage_data,args['stage_name'],params)
    x = np.array(freader.read_section(),np.complex128)

    # get parameters from other stages
    fparams = filedata.get_frame_params(stage_data)
    n_sections = filedata.get_stage_parameter(stage_data,'num_sections')
    Nsuperframe = filedata.get_num_samples_with_framing(stage_data) # it is basically frame_period*num_frames
    assert x.size>=Nsuperframe
    sample_rate = filedata.get_stage_parameter(stage_data,'sample_rate')
    Nsettle = int(params['settle_time'] * sample_rate)

    # Run the emulated channel in GR and save the resulting file in a tmp file
    emulate_repeating_RF_channel(tmp_file,x,fparams,n_sections,Nsuperframe,params,Nsettle)

    # save the results
    success = RF_sync_utils.post_process_rx_file_and_save(stage_data,tmp_file,args,fparams,n_sections,Nsuperframe,Nsettle)
    if success is True:
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later
