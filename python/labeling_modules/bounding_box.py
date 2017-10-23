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

class BoundingBox:
    def __init__(self,time_bounds,freq_bounds):
        self.time_bounds = time_bounds
        self.freq_bounds = freq_bounds
        self.assert_validity()

    def assert_validity(self):
        assert len(self.time_bounds)==2
        assert type(self.time_bounds[0]) is int and type(self.time_bounds[1]) is int
        assert len(self.freq_bounds)==2 and np.max(self.freq_bounds)<=0.5 and np.min(self.freq_bounds)>=-0.5
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

# Helpers for computing bounding boxes

def find_tx_intervals(x):
    thres = 1e-5
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
    return l

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

def debug_freq_bound_finder(X,Xcentre,left_bound,right_bound):
    # print 'cumsums:',csum_left[-1],csum_right[-1]
    XdB = 10*np.log10([max(xx,1.0e-6) for xx in X])
    plt.plot(XdB)
    f_range = range(int(np.round(left_bound)),int(np.round(right_bound))+1)
    plt.plot(f_range,XdB[f_range],'o:')
    plt.plot(int(np.round(Xcentre)),XdB[int(np.round(Xcentre))],'x')
    plt.show()

def find_freq_bounds(x,thresdB=-25):
    # preprocess X in freq domain
    f,X = signal.welch(x,1.0,return_onesided=False,detrend=False)#nperseg=64,noverlap=0
    X = np.fft.fftshift(X)
    Xamp_range = (np.min(X),np.max(X))
    X = (X-Xamp_range[0])/(Xamp_range[1]-Xamp_range[0])

    # compute the centre of mass
    Xcentre = np.argmax(X)#np.sum(np.arange(X.size)*X)/np.sum(X)
    thres = 10**(thresdB/10.0)

    # find left bound
    Xstart = int(np.round(Xcentre-X.size/2))
    Xleftrange = np.mod(range(Xstart,int(np.round(Xcentre))+1),X.size)
    left_bound = next(j for j in Xleftrange if X[j]>thres*X[Xcentre])

    # find right bound
    Xend = int(np.round(Xcentre+X.size/2))
    Xrightrange = np.mod(range(Xend,int(np.round(Xcentre))-1,-1),X.size) # descending order
    right_bound = next(j for j in Xrightrange if X[j]>thres*X[Xcentre])

    interv = ((left_bound-0.5)/float(X.size)-0.5,(right_bound+0.5)/float(X.size)-0.5)
    # debug_freq_bound_finder(X,Xcentre,left_bound,right_bound)
    return interv

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

import time

def compute_bounding_box(x):
    tinterv_list = find_tx_intervals(x)
    finterv = find_freq_bounds(x) # FIXME: Make a smarter frequency estimator that partitions the signal
    # print 'elapsed time(freq intervals):',time.time()-start_time
    boxes = [BoundingBox(i,finterv) for i in tinterv_list]
    return boxes

def select_boxes_that_intersect_section(box_list,section_interv):
    return (b for b in box_list if b.time_intersection(section_interv)!=None)

def add_offset(box_list,toffset=0,foffset=0):
    return (b.add(toffset,foffset) for b in box_list)

def intersect_boxes_with_section(box_list,section_interv):
    w = BoundingBox(section_interv,(-0.5,0.5))
    return (w.box_intersection(b) for b in box_list if w.box_intersection(b)!=None)

def intersect_and_offset_box(box_list,section_interv):
    blist = intersect_boxes_with_section(box_list,section_interv)
    return add_offset(blist,toffset=-section_interv[0])

# def partition_boxes_into_sections(box_list,section_bounds):
#     l = [find_boxes_in_section(box_list,s) for s in section_bounds] # NOTE: Optimization can be done
#     return l

def get_box_limits_in_image(box,section_size,dims):
    # NOTE: section_size is needed for overlapping windows
    xmin = int(np.floor(box.time_bounds[0]*dims[0]/float(section_size)))
    xmax = min(max(int(np.ceil(box.time_bounds[1]*dims[0]/float(section_size))),xmin+1),dims[0])
    ymin = int(np.round((box.freq_bounds[0]+0.5)*dims[1]))
    ymax = max(int(np.round((box.freq_bounds[1]+0.5)*dims[1])+1),ymin+1)
    # assert xmin>=0 and xmax<=dims[0] and ymin>=0 and ymax<=dims[1]
    if xmin<0 or xmax>dims[0] or ymin<0 or ymax>dims[1]:
        print 'this should not have happened'
        print box
        print xmin,xmax,ymin,ymax
        print dims, section_size
        assert 0
    if xmin==dims[0] or ymin==dims[1]: # the rounding makes the bounding box go outside
        return -1,-1,-1,-1
    return xmin,xmax,ymin,ymax
