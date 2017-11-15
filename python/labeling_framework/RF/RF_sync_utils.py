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

import sys
import os
import pickle
import json

from ..labeling_tools.bounding_box import *
from ..labeling_tools import preamble_utils
from ..sig_format import pkl_sig_format
from ..sig_format import sig_data_access as filedata
from ..utils import ssh_utils
from ..core import SessionParams
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def get_recording_params(Nsettle,Nsuperframe,frame_period):
    n_skip_samples = max(Nsettle-frame_period,0)
    n_settle_tmp = Nsettle-n_skip_samples # not making this skipped samples is important to fill the history of the pdetec
    n_rx_samples = Nsuperframe + n_settle_tmp + frame_period + 10 # some padding on the right
    valid_rx_window = (n_settle_tmp,n_rx_samples-frame_period) # the peaks to close to the left are gonna be dropped as they would not create a whole frame
    return (n_skip_samples,n_rx_samples,valid_rx_window)

# it deletes false alarms, peaks found inside the settle time or too close to the end
# it also confirms that the peaks are equidistant
# if the number of peaks is not equal to the expected number of sections, return None
def filter_valid_peaks(detected_peaks,frame_period,n_sections,valid_window):
    # print 'stage1:',len(detected_peaks)
    # ignore frames that were not complete or are in settle region
    peaks = [p for p in detected_peaks if p.tidx < valid_window[1] and p.tidx>=valid_window[0]]
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
def read_file_and_framesync(sourcefilename,targetfilename,fparams,n_sections,Nsuperframe,Nsettle):
    block_size = 100000 # we read in chunks
    thres = [0.14,0.1]
    pdetec = preamble_utils.PreambleDetectorType2(fparams,thres1=thres[0],thres2=thres[1])
    _,n_rx_samples,valid_rx_window = get_recording_params(Nsettle,Nsuperframe,fparams.frame_period)

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
    if nread < n_rx_samples:
        err_msg = 'I was expecting {} samples. Got {} instead.'.format(n_rx_samples,nread)
        logger.exception(err_msg)
        raise AssertionError(err_msg)

    selected_peaks = filter_valid_peaks(pdetec.peaks,fparams.frame_period,n_sections,valid_rx_window)
    if selected_peaks is None:
        return None

    tstart = selected_peaks[0].tidx-fparams.awgn_len
    assert tstart>=0
    y = pkl_sig_format.read_fc32_file(sourcefilename,tstart,Nsuperframe)
    if len(y)!=Nsuperframe:
        err_msg = 'I was expecting {} samples. Got {} instead.'.format(Nsuperframe,len(y))
        logger.exception(err_msg)
        raise AssertionError(err_msg)
    for p in selected_peaks: # correct the offset
        p.tidx -= tstart

    return (tstart, selected_peaks, y)

# post-processing the tmp file and update the metadata file
def post_process_rx_file_and_save(stage_data,rawfile,args,fparams,n_sections,Nsuperframe,Nsettle):
    targetfilename = args['targetfilename']
    stage_name = args['stage_name']

    # read and sync
    ret = read_file_and_framesync(rawfile,targetfilename,fparams,n_sections,Nsuperframe,Nsettle)

    # update staged params
    if ret is not None:
        # tstart = ret[0]
        peak_list = ret[1]
        y = ret[2]

        # assert section_bounds do not go over superframe size
        section_bounds = filedata.get_stage_derived_parameter(stage_data,'section_bounds')
        assert Nsuperframe>=np.max([s[1] for s in section_bounds])

        # write the selected samples and preamble peaks to the target file
        stage_data['IQsamples'] = y
        filedata.set_stage_derived_parameter(stage_data,stage_name,'detected_preambles',peak_list)
        with open(targetfilename,'w') as f:
            pickle.dump(stage_data,f)
        return True
    return False

def setup_remote_rx(sessiondata,hostnames,params_to_send):
    tmp_folder = SessionParams.SessionPaths.tmp_folder(sessiondata)
    tmp_params_file = tmp_folder+'/tmp_params.json'
    remote_session_folder = SessionParams.SessionPaths.remote_session_folder(sessiondata)
    remote_tmp_params_file = remote_session_folder+'/tmp_params.json'
    remote_cmd = "python {}/remote_RF_script.py {}".format(remote_session_folder+'/scripts',remote_tmp_params_file)
    params_to_send['outputfile'] = '{}/tmp.32fc'.format(remote_session_folder)
    clear_cmd = "rm " + remote_tmp_params_file + ' ' + params_to_send['outputfile']

    logger.info('Going to send the params to the remote host')
    # save the params into a local file
    with open(tmp_params_file,'w') as f:
        json.dump(params_to_send,f)
    assert os.path.isfile(tmp_params_file)

    # send the stored params to the remote user 
    if isinstance(hostnames,str):
        hostnames = [hostnames]
    for h in hostnames:
        ssh_utils.scp_send(h,tmp_params_file,remote_tmp_params_file)
    
    # clear local file
    os.remove(tmp_params_file)

    return (remote_cmd,params_to_send['outputfile'],clear_cmd)
