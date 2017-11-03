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
import matplotlib.pyplot as plt
from scipy import signal
import sys
import os
sys.path.append(os.path.abspath('../utils'))
from basic_utils import *

fftsize = 64 # I have to define this somewhere later

class BoundingBox:
    def __init__(self,time_bounds,freq_bounds):
        self.time_bounds = time_bounds
        self.freq_bounds = freq_bounds
        self.assert_validity()

    def assert_validity(self):
        assert len(self.time_bounds)==2
        assert type(self.time_bounds[0]) is int and type(self.time_bounds[1]) is int
        if len(self.freq_bounds)!=2 or np.max(self.freq_bounds)>0.5 or np.min(self.freq_bounds)<-0.5:
            print 'ERROR: The freq bounds: ', self.freq_bounds, ' are not valid.'
            print 'Reconsider a different freq offset range'
            exit(-1)
        assert self.time_bounds[1]>self.time_bounds[0] and self.freq_bounds[1]>self.freq_bounds[0]

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
        return BoundingBox(tintersect,fintersect)

    def add(self,time=0,freq=0):
        tvec = (self.time_bounds[0]+time,self.time_bounds[1]+time)
        fvec = (self.freq_bounds[0]+freq,self.freq_bounds[1]+freq)
        return BoundingBox(tvec,fvec)

    def __str__(self):
        return '[({},{}),({},{})]'.format(self.time_bounds[0],self.time_bounds[1],self.freq_bounds[0],self.freq_bounds[1])

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
    tmin = scale_time(old_sample_bounds[0],new_section_size,old_section_size)
    tmax = scale_time(old_sample_bounds[1]-1,new_section_size,old_section_size)+1
    assert tmax>=tmin+1 and tmin>=0
    tmax = min(tmax,new_section_size)
    if max(tmin,tmax)>new_section_size:
        print 'ERROR: Time window mismatch with the image dimensions'
        print 'tlims:',(tmin,tmax),',window size:',new_section_size
        exit(-1)
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

def compute_boxes_pwr(x, box_list):
    return [np.mean(np.abs(x[b.time_bounds[0]:b.time_bounds[1]])**2) for b in box_list]

# to be finished
class ImageBoundingBox:
    def __init__(self,img_shape,row_bounds,col_bounds):
        self.img_shape = img_shape
        self.row_bounds = row_bounds
        self.col_bounds = col_bounds

    @classmethod
    def convert_from_BoundingBox(cls,bbox,img_shape,section_size):
        rowlims = scale_time_range_to_image_rows(bbox.time_bounds,img_shape[0],section_size)

class Spectrogram:
    def __init__(self,Sxx,section_size):
        self.Sxx = np.fft.fftshift(np.transpose(Sxx),axes=(1,))
        self.section_size = section_size
        self.Sxxnorm = self.normalize()

    def normalize(self):
        Srange = (np.min(self.Sxx),np.max(self.Sxx))
        Snorm = (self.Sxx-Srange[0])/(Srange[1]-Srange[0])
        assert np.max(Snorm)<=1.0 and np.min(Snorm)>=0
        return Snorm

    def matrix(self,normalized=False):
        if normalized==False:
            return self.Sxx
        return self.Sxxnorm

    def time_to_row(self,twin): # time is in sample idx
        return scale_time_bounds(twin,self.Sxx.shape[0],self.section_size)
        # return scale_time_range_to_image_rows(twin,self.Sxx.shape[0],self.section_size)

    def freq_to_col(self,freq_bounds): # freq is normalized to [-0.5,0.5]
        colmin,colmax = freqnorm_to_int_bounds(freq_bounds,self.Sxx.shape[1])
        # colmin = int(np.round((freq_bounds[0]+0.5)*self.Sxx.shape[1]))
        # colmax = max(int(np.round((freq_bounds[1]+0.5)*self.Sxx.shape[1])+1),colmin+1)
        assert colmin>=0 and colmin<=self.Sxx.shape[1]
        assert colmax>=0 and colmax<=self.Sxx.shape[1]
        return (colmin,colmax)

    def bounding_box_coordinates(self,box):
        rows = self.time_to_row(box.time_bounds)
        cols = self.freq_to_col(box.freq_bounds)
        return rows,cols

    def filter_by_time(self,twin,normalized):
        row_range = self.time_to_row(twin)
        if normalized is True:
            return self.Sxxnorm[row_range[0]:row_range[1],:]
        return self.Sxx[row_range[0]:row_range[1],:]

    # gets a list of time windows where the boxes are located, and returns a list with the boxes freq bounds
    def find_freq_bounds(self,twin_list=None,thresdB=-20):
        # convert argument to list
        if twin_list is None:
            twin_list = [(0,self.Sxx.shape[0])] # beginning to end
        if type(twin_list) is tuple:
            assert len(twin_list)==2
            twin_list = [twin_list]

        thres = 10**(thresdB/10.0)
        l = []
        for twin in twin_list:
            S = self.filter_by_time(twin,normalized=True) # S is a spectrogram relative to the twin
            Sfreq = np.max(S,0) # gets maximum for each column

            # centre
            Scentre = np.sum(np.arange(Sfreq.size)*Sfreq)/np.sum(Sfreq)
            # Scentre = np.argmax(Sfreq)
            # Smax = Sfreq[Scentre]
            Sthres = 1*thres
            Ssize = Sfreq.size

            # print 'twin:',twin,'len:',twin[1]-twin[0]
            # plt.imshow(S)
            # plt.show()

            # find left bound
            Sstart = max(int(np.round(Scentre-Ssize/2)),0)
            Sleftrange = np.mod(range(Sstart,int(np.round(Scentre))+1),Ssize)
            # left_bound = next((j for j in Sleftrange if Sfreq[j]>Sthres),Sleftrange[-1])
            left_bound = Sleftrange[first_where(Sfreq[Sleftrange],lambda x: x>Sthres,-1)]

            # find right bound
            Send = min(int(np.round(Scentre+Ssize/2)),Ssize-1)
            Srightrange = np.mod(range(Send,int(np.round(Scentre))-1,-1),Ssize) # descending order
            right_bound = next((j for j in Srightrange if Sfreq[j]>Sthres),Srightrange[-1])
            right_bound += 1 # NOTE: to consistent with ranges/slices

            interv = freqint_to_norm_bounds((left_bound,right_bound),Ssize)
            assert np.max(interv)<=0.5 and np.max(interv)>=-0.5
            l.append(interv)
        return l

    def convert_box_to_coordinates(self,box):
        rowlims = self.time_to_row(box.time_bounds)
        collims = self.freq_to_col(box.freq_bounds)
        # assert xmin>=0 and xmax<=dims[0] and ymin>=0 and ymax<=dims[1]
        if rowlims[0]<0 or rowlims[1]>self.Sxx.shape[0] or collims[0]<0 or collims[1]>self.Sxx.shape[1]:
            print 'ERROR: The row/col lims seem invalid', rowlims, collims, box, Sxx.shape
            exit(-1)
        if rowlims[0]>=self.Sxx.shape[0] or collims[0]>=self.Sxx.shape[1]: # the rounding makes the bounding box go outside
            return -1,-1,-1,-1
        return rowlims[0],rowlims[1],collims[0],collims[1]
    
    @classmethod
    def make_spectrogram(cls,x,fftsize=64,cancel_DC_offset=False):
        _,_,Sxx=signal.spectrogram(x,1.0,noverlap=0,nperseg=fftsize,return_onesided=False,detrend=False)
        if cancel_DC_offset:
            pwr_min = np.min(Sxx)
            Sxx[0,:] = pwr_min # the spectrogram is still not transposed
        return cls(Sxx,x.size)

def find_tx_intervals(xorig,fftsize):
    def merge_close_intervals(l,margin=5):
        l2 = []
        i = 0
        while i < len(l):
            j=i+1
            while j<len(l) and l[j][0]-l[j-1][1] <= margin:
                j+=1
            l2.append((l[i][0],l[j-1][1]))
            i=j
        return l2
    thres = 1e-12
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
        if i2==len(x):
            break
        prev = stepups[j]
        # i = stepups[j+jinc]
    l2 = merge_close_intervals(l,fftsize/2)
    return l2

# Helpers for computing bounding boxes

def compute_bounding_boxes(x):
    fftsize = 64 # NOTE: I have to define this in the sim_awgn_params config file
    time_intervals = find_tx_intervals(x,fftsize)
    Spec = Spectrogram.make_spectrogram(x,fftsize)
    finterv_list = Spec.find_freq_bounds(time_intervals)
    n_boxes = len(time_intervals)
    assert n_boxes == len(finterv_list)
    boxes = [BoundingBox(time_intervals[i],finterv_list[i]) for i in range(n_boxes)]
    # print 'New boxes:',[b.__str__() for b in boxes]
    return boxes

def debug_freq_bound_finder(X,Xcentre,left_bound,right_bound):
    XdB = 10*np.log10([max(xx,1.0e-6) for xx in X])
    plt.plot(XdB)
    f_range = range(int(np.round(left_bound)),int(np.round(right_bound))+1)
    plt.plot(f_range,XdB[f_range],'o:')
    plt.plot(int(np.round(Xcentre)),XdB[int(np.round(Xcentre))],'x')
    plt.show()

import time

# This function simply selects the boxes that touch the time section
def select_boxes_that_intersect_section(box_list,section_interv):
    return (b for b in box_list if b.time_intersection(section_interv)!=None)

# This function adds a time and freq offset
def add_offset(box_list,toffset=0,foffset=0):
    return (b.add(toffset,foffset) for b in box_list)

# This function intersects the boxes with the boundaries of the time section, so nothing leaks
def intersect_boxes_with_section(box_list,section_interv):
    w = BoundingBox(section_interv,(-0.5,0.5))
    return (w.box_intersection(b) for b in box_list if w.box_intersection(b)!=None)

# This function intersects with the boundaries and makes the time offset relative to the beginning of the section
def intersect_and_offset_box(box_list,section_interv):
    blist = intersect_boxes_with_section(box_list,section_interv)
    return add_offset(blist,toffset=-section_interv[0])

#### deprecated

# def find_freq_bounds(x,thresdB=-25):
#     # preprocess X in freq domain
#     f,X = signal.welch(x,1.0,return_onesided=False,detrend=False)#nperseg=64,noverlap=0
#     X = np.fft.fftshift(X)
#     Xamp_range = (np.min(X),np.max(X))
#     X = (X-Xamp_range[0])/(Xamp_range[1]-Xamp_range[0])

#     # compute the centre of mass
#     Xcentre = np.argmax(X)#np.sum(np.arange(X.size)*X)/np.sum(X)
#     thres = 10**(thresdB/10.0)

#     # find left bound
#     Xstart = int(np.round(Xcentre-X.size/2))
#     Xleftrange = np.mod(range(Xstart,int(np.round(Xcentre))+1),X.size)
#     left_bound = next(j for j in Xleftrange if X[j]>thres*X[Xcentre])

#     # find right bound
#     Xend = int(np.round(Xcentre+X.size/2))
#     Xrightrange = np.mod(range(Xend,int(np.round(Xcentre))-1,-1),X.size) # descending order
#     right_bound = next(j for j in Xrightrange if X[j]>thres*X[Xcentre])

#     interv = ((left_bound-0.5)/float(X.size)-0.5,(right_bound+0.5)/float(X.size)-0.5)
#     # debug_freq_bound_finder(X,Xcentre,left_bound,right_bound)
#     return interv

# def create_spectrogram(x,nfft=64):
#     _,_,Sxx=signal.spectrogram(x,1.0,noverlap=0,nperseg=nfft,return_onesided=False,detrend=False)
#     Sxx = np.fft.fftshift(np.transpose(Sxx),axes=(1,))
#     return Sxx

# def find_frequency_bounds(x,fftsize=64,thres=0.001):

#     # preprocess X in freq domain
#     f,X = signal.welch(x,1.0,return_onesided=False,detrend=False)
#     # f,X = signal.periodogram(x,window='blackmanharris',nfft=fftsize,detrend=False,return_onesided=False)
#     X = np.fft.fftshift(X)
#     # X=np.fft.fftshift(np.abs(np.fft.fft(x,fftsize))**2)
#     Xamp_range = (np.min(X),np.max(X))
#     X = (X-Xamp_range[0])/(Xamp_range[1]-Xamp_range[0])

#     # compute the centre of mass
#     Xcentre = np.sum(np.arange(X.size)*X)/np.sum(X)

#     # find left bound
#     Xstart = int(np.round(Xcentre-X.size/2))
#     Xleftrange = np.mod(range(Xstart,int(np.round(Xcentre))+1),X.size)
#     # left_bound = next(i for i in Xleftrange if X[i] > X[Xcentre]*thres)
#     csum_left = np.cumsum(X[Xleftrange])
#     left_bound = next(j+Xstart for j in range(csum_left.size) if csum_left[j]>thres*csum_left[-1])

#     # find right bound
#     Xend = int(np.round(Xcentre+X.size/2))
#     Xrightrange = np.mod(range(int(np.round(Xcentre)),Xend),X.size)
#     # right_bound = next(i for i in Xrightrange if XdB[i] < XdB[Xcentre]*thres)
#     csum_right = np.cumsum(X[Xrightrange])
#     right_bound = next(j+Xcentre for j in range(csum_right.size) if csum_right[j]>=(1-thres)*csum_right[-1])

#     interv = ((left_bound-0.5)/float(X.size)-0.5,(right_bound+0.5)/float(X.size)-0.5)

#     debug_freq_bound_finder(X,Xcentre,left_bound,right_bound,csum_left,csum_right)

#     return interv

# def compute_bounding_box(x):
#     tinterv_list = find_tx_intervals(x)
#     finterv = find_freq_bounds(x) # FIXME: Make a smarter frequency estimator that partitions the signal
#     # print 'elapsed time(freq intervals):',time.time()-start_time
#     boxes = [BoundingBox(i,finterv) for i in tinterv_list]
#     return boxes

# def partition_boxes_into_sections(box_list,section_bounds):
#     l = [find_boxes_in_section(box_list,s) for s in section_bounds] # NOTE: Optimization can be done
#     return l

# def time_to_specgram_row(twin,dims,section_size):
#     rowmin = int(np.floor(twin[0]*dims[0]/float(section_size)))
#     rowmax = max(int(np.ceil(twin[1]*dims[0]/float(section_size))),rowmin+1)
#     rowmax = min(rowmin,dims[0])
#     return (rowmin,rowmax)

# def get_box_limits_in_image(box,section_size,dims):
#     # NOTE: section_size is needed for overlapping windows
#     xmin = int(np.floor(box.time_bounds[0]*dims[0]/float(section_size)))
#     xmax = min(max(int(np.ceil(box.time_bounds[1]*dims[0]/float(section_size))),xmin+1),dims[0])
#     ymin = int(np.round((box.freq_bounds[0]+0.5)*dims[1]))
#     ymax = max(int(np.round((box.freq_bounds[1]+0.5)*dims[1])+1),ymin+1)
#     # assert xmin>=0 and xmax<=dims[0] and ymin>=0 and ymax<=dims[1]
#     if xmin<0 or xmax>dims[0] or ymin<0 or ymax>dims[1]:
#         print 'this should not have happened'
#         print box
#         print xmin,xmax,ymin,ymax
#         print dims, section_size
#         assert 0
#     if xmin>=dims[0] or ymin>=dims[1]: # the rounding makes the bounding box go outside
#         return -1,-1,-1,-1
#     return xmin,xmax,ymin,ymax

# def compute_freq_bounds(x,box_time_bounds,section_size,fftsize=64):
#     thres = 0.1
#     l = []
#     Sxx = create_spectrogram(x,fftsize,normalized=True)
#     for twin in box_time_bounds:
#         row_limits = time_to_spectrogram_row(twin,section_size)
#         box_spectrogram = Sxx[row_limits[0]:row_limits[1],:]
#         for col in Sxx.shape[1]:
#             occupied_idxs = np.where(np.max(box_spectrogram,axis=(0,))>thres)
#             l.append((np.min(occupied_idxs,np.max(occupied_idxs))))
#     return l

# def find_tx_intervals_old(x): # NOTE: For some reason this version although simpler is super slow
#     thres = 1e-5
#     i=0
#     l=[]
#     while i < len(x):
#         try:
#             i = next(j for j in range(i,len(x)) if x[j]>=thres)
#         except StopIteration:
#             break
#         try:
#             i2 = next(j for j in range(i+1,len(x)) if x[j]<thres)
#         except StopIteration:
#             i2=len(x)
#         l.append((i,i2))
#         i = i2+1
#     return l
