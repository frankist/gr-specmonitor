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

import numpy as np
from scipy import signal

import image_representation as imgfmt
import timefreq_box as tfbox
from ..labeling_tools import bounding_box import bndbox
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

##### kind of private methods

def compute_spectrogram(x,fftsize):
    """
    This function creates a single spectrogram based on the provided fftsize
    """
    _,_,Sxx=signal.spectrogram(x,1.0,noverlap=0,nperseg=fftsize,return_onesided=False,detrend=False)
    Sxxshifted = np.fft.fftshift(np.transpose(Sxx),axes=(1,))
    return Sxxshifted

def get_img_bounding_box(timefreq_box,signal_duration,img_shape):
    row_bounds = tfbox.scale_time_bounds(timefreq_box.time_bounds,img_shape[0],signal_duration)
    col_bounds = tfbox.freqnorm_to_int_bounds(timefreq_box.freq_bounds,img_shape[1])
    label = timefreq_box.params.get('label',None)
    return bndbox.ImgBoundingBox(row_bounds[0],row_bounds[1],col_bounds[0],col_bounds[1],img_shape,label)

def compute_PSD_freq_col_bounds(Sfreq,thres):
    Scentre = np.sum(np.arange(Sfreq.size)*Sfreq)/np.sum(Sfreq)
    Sthres = 1*thres
    Ssize = Sfreq.size

    # find left bound
    Sstart = max(int(np.round(Scentre-Ssize/2)),0)
    Sleftrange = np.mod(range(Sstart,int(np.round(Scentre))+1),Ssize)
    left_bound = Sleftrange[first_where(Sfreq[Sleftrange],lambda x: x>Sthres,-1)]

    # find right bound
    Send = min(int(np.round(Scentre+Ssize/2)),Ssize-1)
    Srightrange = np.mod(range(Send,int(np.round(Scentre))-1,-1),Ssize) # descending order
    right_bound = next((j for j in Srightrange if Sfreq[j]>Sthres),Srightrange[-1])
    right_bound += 1 # NOTE: to consistent with ranges/slices

    return (left_bound,right_bound)

def compute_freq_norm_bounds(Sxx_norm, section_size, tinterv_list = None, thresdB=-15):
    def filter_by_time_bound(twin): # time is still in sample idx, rather than row
        row_range = tfbox.scale_time_bounds(twin,Sxx_norm.shape[0],section_size)
        return Sxx_norm[row_range[0]:row_range[1],:]

    # convert argument to list
    if tinterv_list is None:
        tinterv_list = [(0,Sxx_norm.shape[0])] # beginning to end
    assert isinstance(tinterv_list,list)

    thres = 10**(thresdB/10.0)
    l = []
    for twin in tinterv_list:
        Sxx_slice = filter_by_time_bound(twin)
        Sfreq = np.mean(Sxx_slice,axis=0) # Basically the freq. psd

        # these are in column indices
        left_bound,right_bound = compute_PSD_freq_col_bounds(Sfreq,thres)

        # need to conver them to freq_norm
        interv = tfbox.freqint_to_norm_bounds((left_bound,right_bound),Ssize)
        l.append(interv)
    return l

def compute_freq_col_bounds(Sxx_norm, row_bounds = None, thresdB = -15):
    # convert argument to list
    if tinterv_list is None:
        tinterv_list = [(0,Sxx_norm.shape[0])] # beginning to end
    assert isinstance(tinterv_list,list)
    thres = 10**(thresdB/10.0)
    l = []
    for twin in tinterv_list:
        Sxx_slice = Sxx_norm[row_bounds[0]:row_bounds[1],:]
        Sfreq = np.mean(Sxx_slice,axis=0) # Basically the freq. psd

        # these are in column indices
        left_bound,right_bound = compute_PSD_freq_col_bounds(Sfreq,thres)

        # need to conver them to freq_norm
        interv = (left_bound,right_bound)
        l.append(interv)
    return l

def make_normalized_spectrogram_image(x,params):
        fftsize = params.get('fftsize',64)
        cancel_DC_offset = params.get('cancel_DC_offset',False)

        Sxx = compute_spectrogram(x,fftsize)
        if cancel_DC_offset:
            pwr_min = np.min(Sxx)
            Sxx[0,:] = pwr_min # the spectrogram is still not transposed
        Sxxnorm = imgfmt.normalize_image_data(Sxx)
        assert Sxxnorm[0]>=1 and Sxxnorm[1]>=1
        return Sxxnorm

# todelete
def compute_bounding_boxes(Sxx):
    """
    This returns the boxes in row and col format
    """
    xrows = np.mean(Sxx,axis=1)
    row_bounds = tfbox.compute_signal_time_bounds(xrows,0) # no margin
    n_boxes = len(row_bounds)
    col_bounds = compute_freq_col_bounds(self.data,row_bounds)
    assert len(col_bounds)==n_boxes

    boxes = [bndbox.ImgBoundingBox(row_bounds[i][0], row_bounds[i][1],
                            col_bounds[i][0], col_bounds[i][1],
                            Sxx.shape) for i in range(n_boxes)]
    return boxes

def generate_timefreq_boxes(x,params):
    Sxx = SpectrogramImg(x,params)
    time_bounds = tfbox.compute_signal_time_bounds(x,Sxx.fftsize/2)
    n_boxes = len(time_bounds)
    freq_bounds = compute_freq_norm_bounds(Spec.data,len(x),time_bounds)
    assert len(freq_bounds)==n_boxes
    boxes = [TimeFreqBox(time_bounds[i],freq_bounds[i]) for i in range(n_boxes)]
    return boxes

def add_derived_sigdata(stage_data,x,args):
    spec_params = args['parameters']['signal_representation']
    box_label = args['parameters'][Sxx.boxlabel]

    box_list = generate_timefreq_boxes(x,spec_params)

    # normalize the power of the signal and add power as param to each box
    box_pwr_list = tfbox.compute_boxes_pwr(x,box_list)
    max_pwr_box = np.max(box_pwr_list)
    y = x/np.sqrt(max_pwr_box)
    for i in range(len(box_pwr_list)):
        box_list[i].params['power'] = box_pwr_list[i]/max_pwr_box
        box_list[i].params['label'] = box_label

    # fill with samples
    stage_data['IQsamples'] = y
    # add the parameters that were derived
    sda.set_stage_derived_parameter(stage_data, args['stage_name'], 'timefreq_boxes', box_list)

class SpectrogramImgConverter(SignalImgConverter):
    @staticmethod
    def set_derived_sigdata(stage_data,x,args):
        add_derived_sigdata(stage_data,x,args)

    @staticmethod
    def image_data(x,representation_params):
        return make_normalized_spectrogram_image(x,representation_params)

    @staticmethod
    def generate_bounding_boxes(stage_data,stage_name):
        """
        This function assumes the timefreq boxes already exist. We just need to convert them
        """
        pass #FIXME

# register spectrogram as a signal image representation
imgfmt.register_image_representation('spectrogram',SpectrogramImgConverter)

