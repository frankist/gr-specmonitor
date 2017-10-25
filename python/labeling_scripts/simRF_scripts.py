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

# it deletes false alarms, peaks found inside the settle time or too close to the end
# it also confirms that the peaks are equidistant
# if the number of peaks is not equal to the expected number of sections, return None
def filter_valid_peaks(detected_peaks,nread,frame_period,n_sections,Nsettle):
    # print 'stage1:',len(detected_peaks)
    # ignore frames that were not complete or are in settle region
    peaks = [p for p in detected_peaks if p.tidx < nread-frame_period and p.tidx>=Nsettle]
    if len(peaks)<n_sections:
        return None

    # print 'stage2:',len(peaks)
    maxi = np.argmax([np.abs(p.xcorr) for p in peaks])

    # filter out peaks that are not equispaced
    def harmonic_distance(t1,t2,T):
        k = np.round((t1-t2)/T)
        return np.abs(t1-(t2+k*T))
    peaks = [p for p in peaks if harmonic_distance(peaks[maxi].tidx,p.tidx,frame_period)<5]

    # print 'stage3:',len(peaks)
    # we failed to collect the expected number of peaks
    if len(peaks) < n_sections:
        return None

    if len(peaks) > n_sections:
        n_extra = len(peaks)-n_sections
        valmax = (0,0)
        for i in range(n_extra):
            sumtot = np.sum([np.abs(p.xcorr for p in peaks[i:i+n_sections])])
            if sumtot > valmax[1]:
                valmax = (i,sumtot)
        peaks = peaks[valmax[0]:valmax[0]+n_sections]
        assert len(peaks)==n_sections

    # print 'stage4:',len(peaks)
    # sort by time
    idx_sort = np.argsort([peaks[i].tidx for i in range(len(peaks))])
    peaks = [peaks[i] for i in idx_sort]

    return peaks

# read raw samples file and sync with the preambles
def read_file_and_framesync(sourcefilename,targetfilename,frame_params,n_sections,num_samples,Nsettle):
    block_size = 100000 # we read in chunks
    thres = [0.14,0.1]
    pdetec = preamble_utils.PreambleDetectorType2(frame_params,thres1=thres[0],thres2=thres[1])

    # check for peaks in chunks
    i = 0
    nread = 0
    while True:
        samples = pkl_sig_format.read_fc32_file(sourcefilename,i*block_size,block_size)
        if len(samples)==0:
            break
        pdetec.work(samples)
        i += 1
        nread += len(samples)
    assert(nread>=num_samples+Nsettle)

    selected_peaks = filter_valid_peaks(pdetec.peaks,nread,frame_params.frame_period,n_sections,Nsettle)
    if selected_peaks is None:
        return None

    tstart = selected_peaks[0].tidx-frame_params.awgn_len
    assert tstart>=0
    y = pkl_sig_format.read_fc32_file(sourcefilename,tstart,num_samples)
    if len(y)!=num_samples:
        print 'ERROR: this was not the expected size for the samples'
        exit(-1)
    for p in selected_peaks: # correct the offset
        p.tidx -= tstart

    return (tstart, selected_peaks, y)

def emulate_repeating_RF_channel(outputfile,framed_signal,fparams,n_sections,Nsuperframe,params,Nsettle):
    ### Set variables based on given parameters
    tot_linear_gain,noise_voltage = read_and_assert_channel_amplitudes(params)
    freq_offset = params.get('channel_frequency_offset',0)

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
    skip = blocks.skiphead(gr.sizeof_gr_complex,random_TxRx_unsync)
    head = blocks.head(gr.sizeof_gr_complex,Rx_num_samples)
    fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

    tb.connect(source,attenuation)
    tb.connect(attenuation,channel)
    tb.connect(channel,skip)
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

    # post-processing the tmp file and update the metadata file
    ret = read_file_and_framesync(tmp_file,targetfilename,fparams,n_sections,Nsuperframe,Nsettle)
    if ret is not None:
        # write file and discard padding samples
        tstart = ret[0]
        peak_list = ret[1]
        y = ret[2]
        section_bounds = filedata.get_stage_derived_parameter(stage_data,'section_bounds')
        assert Nsuperframe>=np.max([s[1] for s in section_bounds])

        stage_data['IQsamples'] = y
        filedata.set_stage_derived_parameter(stage_data,args['stage_name'],'detected_preambles',peak_list)
        with open(targetfilename,'w') as f:
            pickle.dump(stage_data,f)
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later

    # ### Set variables based on given parameters
    # sample_rate = filedata.get_stage_parameter(stage_data,'sample_rate')
    # Nsettle = int(params['settle_time'] * sample_rate)
    # tot_linear_gain = 10**((params['tx_gaindB']+params['rx_gaindB']-params['PLdB'])/20.0)
    # noise_voltage = 10**((params['awgndBm']-30)/20.0)
    # freq_offset = args.get('channel_frequency_offset',0)

    # ### Read Signal already Framed and apply channel effects and settle time and writes to a temp file
    # x = freader.read_section()
    # x_with_settle = np.append(np.zeros(Nsettle,np.complex64),x)
    # x_with_settle = np.append(x_with_settle,np.zeros(int(Nsettle/2),np.complex64)) # padding at the end

    # # it is possible the preamble sync fails. In such case, no file is gonna be written
    # rf_flowgraph = RF2FileFlowgraph(x_with_settle,tot_linear_gain,noise_voltage,freq_offset,tmp_file)
    # rf_flowgraph.run() # this will stop after a while

    # ### Read the temporary file, syncs, and writes the pickle
    # fparams = filedata.get_frame_params(stage_data)
    # n_sections = filedata.get_stage_parameter(stage_data,'num_sections')
    # num_samples = filedata.get_num_samples_with_framing(stage_data)
    # ret = file_framesync(tmp_file,targetfilename,fparams,n_sections,num_samples)
    # if ret is not None:
    #     # write file and discard padding samples
    #     tstart = ret[0]
    #     peak_list = ret[1]
    #     y = ret[2]
    #     section_bounds = filedata.get_stage_derived_parameter(stage_data,'section_bounds')
    #     assert num_samples>=np.max([s[1] for s in section_bounds])

    #     stage_data['IQsamples'] = y
    #     # stage_data['IQsamples_per_section'] = [y[s[0]:s[1]] for s in section_bounds]
    #     # del stage_data['IQsamples']
    #     filedata.set_stage_derived_parameter(stage_data,args['stage_name'],'detected_preambles',peak_list)
    #     with open(targetfilename,'w') as f:
    #         pickle.dump(stage_data,f)
    #     print 'STATUS: Finished writing to file',targetfilename
    # else:
    #     print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    # os.remove(tmp_file)
    # # Note: The separation into multiple subsections happens later
