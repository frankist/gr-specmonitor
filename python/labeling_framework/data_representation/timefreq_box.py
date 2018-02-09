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

from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

'''
Represents time through sample indices and freq through the normalized [-0.5,0.5] space
'''
class TimeFreqBox:
    def __init__(self,time_bounds,freq_norm_bounds,label=None):
        TimeFreqBox.assert_validity(time_bounds,freq_norm_bounds)
        self.time_bounds = time_bounds
        self.freq_bounds = tuple([float(f) for f in freq_norm_bounds])
        self.params = {} # other params like power or label
        self.params['label'] = label

    @staticmethod
    def assert_validity(time_bounds,freq_bounds):
        err_test = True
        err_test &= len(time_bounds)==2
        err_test &= isinstance(time_bounds,tuple)
        err_test &= isinstance(time_bounds[0],int)
        err_test &= time_bounds[1]>time_bounds[0]
        err_test &= len(freq_bounds)==2
        err_test &= isinstance(freq_bounds,tuple)
        err_test &= isinstance(freq_bounds[0],float)
        err_test &= np.max(freq_bounds)<=0.5
        err_test &= np.min(freq_bounds)>=-0.5
        err_test &= freq_bounds[1]>freq_bounds[0]
        if err_test==False:
            err_msg = 'The time/freq bounds [{},{}] are not valid.'.format(time_bounds,freq_bounds)
            logger.error(err_msg)
            logger.error('Reconsider changing the waveform params (freq offset range/signal duration)')
            raise AssertionError(err_msg)

    def label(self):
        return self.params['label']

    def set_label(self,lbl):
        self.params['label'] = lbl

    def is_equal(self,box):
        return box.time_bounds==self.time_bounds and box.freq_bounds==self.freq_bounds

    def time_intersection(self,tinterv):
        tstart = max(tinterv[0],self.time_bounds[0])
        tend = min(tinterv[1],self.time_bounds[1])
        if tend<=tstart:
            return None
        return (tstart,tend)

    def freq_intersection(self,finterv):
        fstart = max(finterv[0],self.freq_bounds[0])
        fend = min(finterv[1],self.freq_bounds[1])
        if fend<=fstart:
            return None
        return (fstart,fend)

    def box_intersection(self,box):
        tintersect = self.time_intersection(box.time_bounds)
        if tintersect is None:
            return None
        fintersect = self.freq_intersection(box.freq_bounds)
        if fintersect is None:
            return None
        assert self.label() is None or box.label() is None or self.label()==box.label()
        new_label = self.label() if self.label() is not None else box.label()
        return TimeFreqBox(tintersect,fintersect,new_label)

    def add(self,time=0,freq=0):
        tvec = (self.time_bounds[0]+time,self.time_bounds[1]+time)
        fvec = (self.freq_bounds[0]+freq,self.freq_bounds[1]+freq)
        return TimeFreqBox(tvec,fvec,self.label())

    def __str__(self):
        return '[({},{}),({},{})]'.format(self.time_bounds[0],self.time_bounds[1],self.freq_bounds[0],self.freq_bounds[1])

############ Operations over TimeFreqBox ####################

# This function simply selects the boxes that touch the time section
def select_boxes_that_intersect_section(box_list,section_interv):
    return (b for b in box_list if b.time_intersection(section_interv)!=None)

# This function adds a time and freq offset
def add_offset(box_list,toffset=0,foffset=0):
    return (b.add(toffset,foffset) for b in box_list)

# This function intersects the boxes with the boundaries of the time section, so nothing leaks
def intersect_boxes_with_section(box_list,section_interv):
    w = TimeFreqBox(section_interv,(-0.5,0.5))
    return (w.box_intersection(b) for b in box_list if w.box_intersection(b)!=None)

# This function intersects with the boundaries and makes the time offset relative to the beginning of the section
def intersect_and_offset_box(box_list,section_interv,freq_offset=0):
    """
    This function picks a timefreq_box list, and intersects the boxes with a
    section time window. The boxes should not go out of the boundaries. So, their final duration may be different.
    We then compensate the boxes' offset, to make their start relative to the section boundaries
    """
    blist = intersect_boxes_with_section(box_list,section_interv)
    return list(add_offset(blist,toffset=-section_interv[0],foffset=freq_offset))

######## Conversion Normalized to Integer Frequency #############

# freqnorm: [-0.5,0.5] and it is totally symmetric (0 means DC)
# freqint: [0,fftsize] and the DC is at fftsize/2
def freqnorm_to_int(freqnorm,dft_size):
    return int(np.round((freqnorm+0.5)*dft_size+0.5))

def freqnorm_to_int_bounds(freqnorm_range, dft_size):
    fmin = freqnorm_to_int(freqnorm_range[0],dft_size)
    fmax = freqnorm_to_int(freqnorm_range[1],dft_size)
    return (fmin,fmax)

def freqint_to_norm(freqint,dft_size):
    return max((freqint-0.5)/float(dft_size)-0.5,-0.5)

def freqint_to_norm_bounds(freqint_bounds,dft_size):
    fmin = freqint_to_norm(freqint_bounds[0],dft_size)
    fmax = freqint_to_norm(freqint_bounds[1],dft_size)
    return (fmin,fmax)

def scale_time(sample_idx,new_section_size,old_section_size):
    return int(np.round(sample_idx)*new_section_size/float(old_section_size))

def scale_time_bounds(old_sample_bounds,new_section_size,old_section_size):
    """
    You can use this function to convert from sample idx to Spectrogram row
    """
    tmin = scale_time(old_sample_bounds[0],new_section_size,old_section_size)
    tmax = scale_time(old_sample_bounds[1]-1,new_section_size,old_section_size)+1
    assert tmax>=tmin+1 and tmin>=0
    tmax = min(tmax,new_section_size)
    if max(tmin,tmax)>new_section_size:
        logger.error('Time window mismatch with the image dimensions. tlims: {},new window size:{},old sample_bounds:{},old section size:{}'.format((tmin,tmax),new_section_size,old_sample_bounds,old_section_size))
        raise AssertionError('The scaling of the time bounds failed')
    return (tmin,tmax)

# Utils to convert bounding box to image bounding box
def scale_time_range_to_image_rows(trange,nrows,section_size):
    assert np.max(trange)<=section_size
    rowmin = int(np.floor(trange[0]*nrows/float(section_size)))
    rowmax = max(int(np.ceil(trange[1]*nrows/float(section_size))),rowmin+1)
    rowmax = min(rowmax,nrows)
    if min(rowmin,rowmax)<0 and max(rowmin,rowmax)>nrows:
        print 'ERROR: Time window mismatch with the image dimensions'
        print 'rowlims:',(rowmin,rowmax),',nrows:',nrows
        exit(-1)
    return (rowmin,rowmax)

######## Helper functions to handle signals ###########

def compute_boxes_pwr(x, box_list):
    # NOTE: I convert to float bc I want the json of the labels to look nice
    return [float(np.mean(np.abs(x[b.time_bounds[0]:b.time_bounds[1]])**2)) for b in box_list]

def normalize_boxes_pwr(box_list, x):
    box_pwr_list = compute_boxes_pwr(x,box_list)
    max_pwr_box = np.max(box_pwr_list)
    for i in range(len(box_pwr_list)):
        box_list[i].params['power'] = box_pwr_list[i]/max_pwr_box
    return (box_list,max_pwr_box)

def compute_signal_time_bounds(xorig,dist_margin=0,thres=1e-12):
    """
    Compute the time domain boundaries of a signal. Returns in sample idx format.
    You can set a margin to merge boundaries that are too close to each other
    """
    def merge_close_intervals(l,margin):
        l2 = []
        i = 0
        while i < len(l):
            j=i+1
            while j<len(l) and l[j][0]-l[j-1][1] <= margin:
                j+=1
            l2.append((l[i][0],l[j-1][1]))
            i=j
        return l2

    x = np.abs(xorig)**2

    stepups=[i+1 for i in range(len(x)-1) if x[i]<thres and x[i+1]>=thres]
    stepdowns=[i+1 for i in range(len(x)-1) if x[i]>=thres and x[i+1]<thres]
    n_intervs = max(len(stepups),len(stepdowns))
    if x[0]>=thres and x[-1]>=thres:
        n_intervs += 1
    prev = 0
    l = [None]*n_intervs
    for j in range(len(l)):
        i2 = stepdowns[j] if j<len(stepdowns) else len(x)
        i = stepups[j] if j<len(stepups) and stepups[j]<i2 else prev
        l[j] = (i,i2)
        if i2==len(x) or j>=len(stepups):
            break
        prev = stepups[j]
        # i = stepups[j+jinc]
    l2 = merge_close_intervals(l,dist_margin)
    return l2
