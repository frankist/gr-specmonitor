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

from ..utils import basic_utils
import image_representation as imgfmt
import timefreq_box as tfbox
from ..labeling_tools import bounding_box as bndbox
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

##### kind of private methods

def compute_spectrogram(x,fftsize):
    """
    This function creates a single spectrogram based on the provided fftsize
    """
    _,_,Sxx=signal.spectrogram(x,1.0,noverlap=0,nperseg=fftsize,return_onesided=False,detrend=False)
    Sxxshifted = np.fft.fftshift(np.transpose(Sxx),axes=(1,))
    assert Sxxshifted.shape[0]>=1 and Sxxshifted.shape[1]>=1
    return Sxxshifted

def get_img_bounding_box(timefreq_box,signal_duration,img_shape):
    row_bounds = tfbox.scale_time_bounds(timefreq_box.time_bounds,img_shape[0],signal_duration)
    col_bounds = tfbox.freqnorm_to_int_bounds(timefreq_box.freq_bounds,img_shape[1])
    label = timefreq_box.label()
    return bndbox.ImgBoundingBox(row_bounds[0],row_bounds[1],col_bounds[0],col_bounds[1],img_shape,label)

def compute_PSD_freq_col_bounds(Sfreq,thres):
    Scentre = np.sum(np.arange(Sfreq.size)*Sfreq)/np.sum(Sfreq)
    Sthres = 1*thres
    Ssize = Sfreq.size

    # find left bound
    Sstart = max(int(np.round(Scentre-Ssize/2)),0)
    Sleftrange = np.mod(range(Sstart,int(np.round(Scentre))+1),Ssize)
    left_bound = Sleftrange[basic_utils.first_where(Sfreq[Sleftrange],lambda x: x>Sthres,-1)]

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
        Ssize = Sfreq.size

        # these are in column indices
        left_bound,right_bound = compute_PSD_freq_col_bounds(Sfreq,thres)

        # need to conver them to freq_norm
        interv = tfbox.freqint_to_norm_bounds((left_bound,right_bound),Ssize)
        l.append(interv)
    return l

def compute_freq_col_bounds(Sxx_norm, row_bounds = None, thresdB = -15):
    # convert argument to list
    if row_bounds is None:
        row_bounds = [(0,Sxx_norm.shape[0])] # beginning to end
    assert isinstance(row_bounds,list)
    thres = 10**(thresdB/10.0)
    l = []
    for row_win in row_bounds:
        Sxx_slice = Sxx_norm[row_win[0]:row_win[1],:]
        Sfreq = np.mean(Sxx_slice,axis=0) # Basically the freq. psd

        # these are in column indices
        left_bound,right_bound = compute_PSD_freq_col_bounds(Sfreq,thres)

        # need to conver them to freq_norm
        interv = (left_bound,right_bound)
        l.append(interv)
    return l

def normalize_spectrogram(Sxx):
    return imgfmt.normalize_image_data(Sxx)

def cancel_spectrogram_DCoffset(Sxx):
    pwr_min = np.min(Sxx)
    Sxx[:,Sxx.shape[1]/2] = pwr_min
    return Sxx

def convert_timefreq_to_bounding_box(box,img_size,section_size):
    row_lims = tfbox.scale_time_bounds(box.time_bounds,img_size[0],section_size)
    col_lims = tfbox.freqnorm_to_int_bounds(box.freq_bounds,img_size[1])
    return bndbox.ImgBoundingBox(row_lims[0],row_lims[1],col_lims[0],col_lims[1],img_size,box.label())

# timefreq_box is very dependent on the spectrogram parameters. The two concepts are coupled
def compute_timefreq_boxes(x,spec_params):
    # get non-time averaged spectrogram
    Sxx = compute_spectrogram(x,spec_params['fftsize'])
    Sxx = normalize_spectrogram(Sxx)
    if spec_params.get('cancel_DC_offset',False)==True:
        Sxx = cancel_spectrogram_DCoffset(Sxx)

    time_bounds = tfbox.compute_signal_time_bounds(x,Sxx.shape[1]/2)
    n_boxes = len(time_bounds)
    freq_bounds = compute_freq_norm_bounds(Sxx,len(x),time_bounds)
    assert len(freq_bounds)==n_boxes
    boxes = [tfbox.TimeFreqBox(time_bounds[i],freq_bounds[i]) for i in range(n_boxes)]
    return boxes

def time_average_Sxx(Sxx,num_averages,step):
    if num_averages==1 and step==1:
        return Sxx
    n_rows = int(np.floor((Sxx.shape[0]-(num_averages-step))/step))
    Syy = np.zeros((n_rows,Sxx.shape[1]))

    for r in range(Syy.shape[0]):
        Syy[r,:] = np.mean(Sxx[r*step:r*step+num_averages,:],axis=0)

    return Syy

# class SpectrogramImgConverter(SignalImgConverter):
#     @staticmethod
#     def generate_unlabeled_timefreq_boxes(x,params):
#         return compute_timefreq_boxes(x,params)

#     @staticmethod
#     def image_data(x,representation_params):
#         return make_normalized_spectrogram_image(x,representation_params)

#     @staticmethod
#     def generate_img_data_and_bounding_boxes(section,params,tfreq_boxes=[]):
#         """
#         This function assumes the timefreq boxes already exist. We just need to convert them
#         """
#         Sxx = SpectrogramImgConverter.image_data(x,params)
#         bbox_list = [convert_timefreq_to_bounding_box(b,Sxx.shape,x.size) for b in tfreq_boxes]
#         return Sxx,bbox_lsit

class SectionSpectrogramMetadata(object):
    def __init__(self,tfreq_boxes,section_bounds,input_params):
        self.input_params = input_params
        self.tfreq_boxes = tfreq_boxes
        self.section_bounds = section_bounds
        self.depth = 1
        self.fftsize = self.input_params['fftsize']
        self.num_fft_avgs = 1
        self.num_fft_step = 1

    def img_size(self):
        # This is the number of rows without any averaging
        num_rows = int(np.ceil((self.section_duration()-self.fftsize)/float(self.fftsize)))
        # we apply the averaging now
        num_rows = int(np.floor((num_rows-(self.num_fft_avgs-self.num_fft_step))/self.num_fft_step))
        return (num_rows,self.fftsize)

    def section_duration(self):
        return self.section_bounds[1]-self.section_bounds[0]

    def image_data(self,x):
        section = x[self.section_bounds[0]:self.section_bounds[1]]
        Sxx = compute_spectrogram(section, self.input_params['fftsize'])
        Sxx = time_average_Sxx(Sxx,self.num_fft_avgs,self.num_fft_step)
        Sxx = normalize_spectrogram(Sxx)
        if self.input_params.get('cancel_DC_offset',False)==True:
            Sxx = cancel_spectrogram_DCoffset(Sxx)
        if Sxx.shape!=self.img_size():
            logger.error('These were the shapes:{},{}'.format(Sxx.shape,self.img_size()))
            raise AssertionError('Mismatch in spectrogram dimensions: {}!={}. Your section had a duration of {} although it should have {}.'.format(Sxx.shape,self.img_size(),section.size,self.section_duration()))
        return Sxx

    def generate_img_bounding_boxes(self):
        bbox_list = [convert_timefreq_to_bounding_box(b,self.img_size(),self.section_duration()) for b in self.tfreq_boxes]
        return bbox_list

    def set_num_fft_averages(self,Nfftwin,Nfftstep):
        self.num_fft_avgs = Nfftwin
        self.num_fft_step = Nfftstep
        assert self.img_size()[0]>0

    def filter_boxes(self):
        self.tfreq_boxes = tfbox.intersect_and_offset_box(self.tfreq_boxes,self.section_bounds)
        self.assert_validity()

    def slice_section(self,idx_start,idx_stop):
        assert min(idx_start,idx_stop)>=self.section_bounds[0] and max(idx_stop,idx_start)<=self.section_bounds[1]
        assert idx_stop>idx_start

        self.section_bounds = (idx_start,idx_stop)
        self.filter_boxes()

    def slice_by_img_dims(self,idx_start,idx_stop):
        imgsize = self.img_size()
        assert min(idx_start,idx_stop)>=0 and max(idx_start,idx_stop)<=imgsize[0]
        assert idx_stop>idx_start

        # new section
        section_dur = self.section_duration()
        new_section_start = int(section_dur*idx_start/float(imgsize[0])) + self.section_bounds[0]
        new_section_stop = int(section_dur*idx_stop/float(imgsize[0])) + self.section_bounds[0]

        # update section_bounds
        self.section_bounds = (new_section_start,new_section_stop)
        self.filter_boxes()

    def assert_validity(self):
        for b in self.tfreq_boxes:
            test1 = min(b.time_bounds[0],b.time_bounds[1])>=0
            test1 &= max(b.time_bounds[0],b.time_bounds[1])<=self.section_duration()
            if test1==False:
                logger.error('These were the dims:{},{}'.format(b.time_bounds,self.section_duration()))
                raise AssertionError('The boxes do not fit in the section provided.')

    @classmethod
    def generate_metadata(cls,x,section_bounds,input_params,label):
        tfreq_boxes = compute_timefreq_boxes(x,input_params) # these are unlabeled

        for i in range(len(tfreq_boxes)):
            tfreq_boxes[i].set_label(label)

        return cls(tfreq_boxes,section_bounds,input_params)

# register spectrogram as a signal image representation
imgfmt.register_signal_to_img_converter('spectrogram',SectionSpectrogramMetadata)
