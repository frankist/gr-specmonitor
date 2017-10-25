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
