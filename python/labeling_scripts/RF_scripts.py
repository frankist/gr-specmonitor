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

def run_RF_Tx_on_repeat(framed_signal,params,fparams,sample_rate):
    ### Set variables based on given parameters
    gaindB = params['tx_gaindB']
    centre_freq = params['centre_frequency']

    # read samples already framed, apply USRP params, and keep transmitting until interruption
    tb = gr.top_block()
    vector_source = blocks.vector_source_c(framed_signal,True) # keep repeating
    usrp_sink = uhd.usrp_sink(
        ",".join(("", "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    usrp_sink.set_samp_rate(sample_rate)
    usrp_sink.set_center_freq(centre_freq,0)
    usrp_sink.set_gain(gaindB,0)

    connect(vector_source,(usrp_sink,0))
    tb.run()

def run_RF_Rx_for_on_repeat(params,sample_rate,Nsuperframe,Nsettle):
    ### Set variables based on given stage parameters
    gaindB = params['rx_gaindB']
    centre_freq = params['centre_frequency']

    # get the needed global parameters
    frame_period = fparams.frame_period
    Rx_num_samples = Nsuperframe+Nsettle # the settle is important both for the HW and pdetec history
    Rx_num_samples += frame_period + 10 # we will only choose peaks whose frame is whole. I just add an guard interval of a few samples

    tb = gr.top_block()
    usrp_source = uhd.usrp_source(
        ",".join(("", "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    usrp_source.set_samp_rate(sample_rate)
    usrp_source.set_center_freq(centre_freq,0)
    usrp_source.set_gain(gaindB,0)
    head = blocks.head(gr.sizeof_gr_complex,Rx_num_samples)
    fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

    tb.connect(usrp_source,head)
    tb.connect(head,fsink)

    tb.run()

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

    # call here the Tx or Rx scripts

    # save the results
    success = RF_sync_utils.post_process_rx_file_and_save(stage_data,tmp_file,args,fparams,n_sections,Nsuperframe,Nsettle)
    if success is True:
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later
