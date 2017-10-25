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

def read_channel_amplitudes(stage_params):
    config_params = ['txgaindB','rxgaindB','PLdB','awgndBm']
    def contains_any(any_of_these,container):
        return any([s in container for s in any_of_these])

    if 'SNRdB' in stage_params:
        if any([p in stage_params for p in config_params]):
            print 'ERROR: You either define the SNRdB of the channel or the hardware gains and pathloss'
            exit(-1)
        noise_voltage = 1.0
        tot_linear_gain = 10**(stage_params['SNRdB']/20.0)
    elif all([p in stage_params for p in config_params]):
        noise_voltage = 10**((params['awgndBm']-30)/20.0)
        tot_linear_gain = 10**((params['tx_gaindB'+params['rx_gaindB']-params['PLdB']])/20.0)
    else:
        print 'ERROR: You didn\'t specify the required parameters for the channel'
        exit(-1)

    return (tot_linear_gain,noise_voltage)

def emulate_RF_channel(framed_signal,stage_data,params):
    ### Set variables based on given parameters
    sample_rate = filedata.get_stage_parameter(stage_data,'sample_rate')
    num_samples_settle = int(params['settle_time'] * sample_rate)
    tot_linear_gain,noise_voltage = read_channel_amplitudes(params)
    freq_offset = args.get('channel_frequency_offset',0)

    ### Read Signal already Framed and apply channel effects and settle time and writes to a temp file
    x = freader.read_section()
    x_with_settle = np.append(np.zeros(num_samples_settle,np.complex64),x)
    x_with_settle = np.append(x_with_settle,np.zeros(int(num_samples_settle/2),np.complex64)) # padding at the end

    # GNURadio Flowgraph
    tb = gr.top_block()

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

def file_framesync(sourcefilename,targetfilename,frame_params,n_sections,num_samples):
    block_size = 100000
    thres = [0.14,0.1]
    pdetec = preamble_utils.PreambleDetectorType2(frame_params,thres1=thres[0],thres2=thres[1])

    # check for peaks in chunks
    i = 0
    while True:
        samples = pkl_sig_format.read_fc32_file(sourcefilename,i*block_size,block_size)
        if len(samples)==0:
            break
        pdetec.work(samples)
        i += 1

    if len(pdetec.peaks)==n_sections:
        selected_peak_idxs = np.argsort([p.xcorr for p in pdetec.peaks])[-n_sections::]
        # TODO: check if they are at equivalent distances
        idx_sort = np.argsort([pdetec.peaks[i].tidx for i in selected_peak_idxs])
        peaks_selected = [pdetec.peaks[selected_peak_idxs[i]] for i in idx_sort]

        tstart = peaks_selected[0].tidx-frame_params.awgn_len
        y = pkl_sig_format.read_fc32_file(sourcefilename,tstart,num_samples)
        if len(y)!=num_samples:
            print 'ERROR: this was not the expected size for the samples'
            exit(-1)
        for p in peaks_selected: # correct the offset
            p.tidx -= tstart

        return (tstart, peaks_selected, y)

    return None

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

    ### Set variables based on given parameters
    sample_rate = filedata.get_stage_parameter(stage_data,'sample_rate')
    num_samples_settle = int(params['settle_time'] * sample_rate)
    tot_linear_gain = 10**((params['tx_gaindB']+params['rx_gaindB']-params['PLdB'])/20.0)
    noise_voltage = 10**((params['awgndBm']-30)/20.0)
    freq_offset = args.get('channel_frequency_offset',0)

    ### Read Signal already Framed and apply channel effects and settle time and writes to a temp file
    x = freader.read_section()
    x_with_settle = np.append(np.zeros(num_samples_settle,np.complex64),x)
    x_with_settle = np.append(x_with_settle,np.zeros(int(num_samples_settle/2),np.complex64)) # padding at the end

    # it is possible the preamble sync fails. In such case, no file is gonna be written
    rf_flowgraph = RF2FileFlowgraph(x_with_settle,tot_linear_gain,noise_voltage,freq_offset,tmp_file)
    rf_flowgraph.run() # this will stop after a while

    ### Read the temporary file, syncs, and writes the pickle
    fparams = filedata.get_frame_params(stage_data)
    n_sections = filedata.get_stage_parameter(stage_data,'num_sections')
    num_samples = filedata.get_num_samples_with_framing(stage_data)
    ret = file_framesync(tmp_file,targetfilename,fparams,n_sections,num_samples)
    if ret is not None:
        # write file and discard padding samples
        tstart = ret[0]
        peak_list = ret[1]
        y = ret[2]
        section_bounds = filedata.get_stage_derived_parameter(stage_data,'section_bounds')
        assert num_samples>=np.max([s[1] for s in section_bounds])

        stage_data['IQsamples'] = y
        # stage_data['IQsamples_per_section'] = [y[s[0]:s[1]] for s in section_bounds]
        # del stage_data['IQsamples']
        filedata.set_stage_derived_parameter(stage_data,args['stage_name'],'detected_preambles',peak_list)
        with open(targetfilename,'w') as f:
            pickle.dump(stage_data,f)
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later
