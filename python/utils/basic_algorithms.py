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

class moving_average:
    def __init__(self,size,arraytype=np.float32):
        self.xhist = np.zeros(size-1,dtype=arraytype)
        self.size = size

    def work(self,x):
        assert len(x)>1
        xtot = np.append(self.xhist,x)
        y = np.array([np.mean(xtot[i:i+self.size]) for i in range(len(x))])
        self.xhist = xtot[xtot.size-self.size+1::]
        return y

def moving_average_with_hist(x_h,mavgsize):
    assert x_h.hist_len>=mavgsize
    xmavg = np.zeros(x_h.size,dtype=x_h.dtype)
    for i in range(x_h.size):
        xmavg[i] = np.mean(x_h[i-mavgsize:i])
    return xmavg

def moving_average_no_hist(x,size):
    return np.array([np.mean(x[i:i+size]) for i in range(x.size-size)])

# Find the local maximum within boundaries defined by "margin": [-margin,margin]

# tested.
def compute_local_maxima(x,margin): # does not consider history
    i = 0
    i_end = x.size-margin
    l = []
    while i < i_end:
        maxi = np.argmax(x[i+1:i+margin])
        maxi += (i+1)
        if x[maxi]>=x[i]:
            i = maxi
            continue
        l.append(i)
        i += margin
    return (l,i) # I pass the local max position and the point where it stopped evaluating.

# untested
class sliding_window_max: # this works with any array but keeps a buffer
    def __init__(self,margin,dtype=np.float32):
        self.xhist = np.zeros(margin-1,dtype=dtype)
        self.margin = margin

    def work(self,x):
        xtot = np.append(self.xhist,x)
        i = 0
        i_end = xtot.size-self.margin+1
        l = []
        while i < i_end:
            maxi = np.argmax(xtot[i+1:i+margin])
            maxi += (i+1)
            if x[maxi]>=x[i]:
                i = maxi
                continue
            l.append((i-self.margin+1,x[i]))
            i+=margin
        self.xhist = xtot[i::]
        return l

#tested
class sliding_window_max_hist: # this only works with an array with history
    def __init__(self,margin,dtype=np.float32):
        self.margin = margin
        self.xidx = 0

    def work(self,x_h):
        assert x_h.hist_len>=self.margin
        i_end = x_h.size-self.margin
        l = []
        while self.xidx < i_end:
            maxi = np.argmax(x_h[self.xidx+1:self.xidx+self.margin])
            maxi += (self.xidx+1)
            if x_h[maxi]>=x_h[self.xidx]:
                self.xidx = maxi
                continue
            l.append(self.xidx)
            self.xidx+=self.margin
        self.xidx -= x_h.size # starts from a negative point, most of the time at "-margin"
        return l

class filter_ccc:
    def __init__(self,taps):
        self.taps = taps
        self.size = len(taps)
        self.xhist = np.zeros(self.size-1,np.complex64)

    def work(self,x):
        xtot = np.append(self.xhist,x)
        y = np.correlate(xtot,self.taps)
        self.xhist = xtot[xtot.size-self.size+1::]
        return y

# tested 
def compute_schmidl_cox_peak(x,nBins_half):
    dim = x.size-2*nBins_half+1
    delayed_xmult = np.zeros(dim,dtype='complex64')
    for k in range(dim):
        delayed_xmult[k] = np.sum(x[k:k+nBins_half]*np.conj(x[k+nBins_half:k+2*nBins_half]))
    return delayed_xmult

def compute_schmidl_cox_cfo(cplx_vec,nBins_half):
    return -np.angle(cplx_vec)/(2*np.pi*nBins_half)

def compute_schmidl_cox_with_hist(x_h,nBins_half):
    return compute_schmidl_cox_peak(x_h[-nBins_half*2+1:x_h.size],nBins_half)

# tested
def interleaved_crosscorrelate(x1,x2,interleav_len):
    winsize = interleav_len*len(x2)
    y = np.zeros(x1.size-winsize, dtype=np.complex64)
    for i in range(y.size):
        xx = x1[i:i+winsize:interleav_len]
        y[i] = np.sum(xx*x2)
    return y

# tested
def interleaved_crosscorrelate_with_hist(x_h,x2,interleav_len):
    winsize = interleav_len*len(x2)
    x = x_h[-winsize:x_h.size]
    return interleaved_crosscorrelate(x,x2,interleav_len)

def interleaved_sum(x1,num_sums,interleav_len):
    winsize = interleav_len*num_sums
    y = np.zeros(x1.size-winsize,dtype=np.complex64)
    for i in range(y.size):
        xx = x1[i:i+winsize:interleav_len]
        y[i] = np.sum(np.abs(xx))
    return y

# arguments are in the freq domain
def zc_cfo_estimation_freq(X,PSEQ): # works with ZadoffChu
    Xdot = X*np.conj(PSEQ)
    # plt.plot(np.angle(Xdot*np.conj(np.roll(Xdot,1))))
    Xshift = np.sum(Xdot*np.conj(np.roll(Xdot,1)))
    return -np.angle(Xshift)/(2*np.pi)

# something seems wrong here
def interleaved_zc_cfo_estimation(x,pseq,Ntimes):
    import matplotlib.pyplot as plt
    PSEQ = np.fft.fft(pseq)
    cfo_list = []
    for i in range(Ntimes):
        cfo_list.append(zc_cfo_estimation_freq(x[i*PSEQ.size:(i+1)*PSEQ.size],PSEQ))
    # plt.plot(cfo_list)
    # plt.show()
    return np.mean(cfo_list)

# obsolete
def interleaved_crosscorrelate_rotated(x1,x2,interleav_len):
    winsize = interleav_len*len(x2)
    y = np.zeros(x1.size-winsize, dtype=np.complex64)
    xangleshift = np.zeros(x1.size-winsize)
    for i in range(y.size):
        xx = x1[i:i+winsize:interleav_len]
        xmult = xx*np.conj(x2)
        xangleshift[i] = np.angle(np.sum(xmult[1::]*np.conj(xmult[0:-1])))
        y[i] = np.sum(xx*np.exp(-1j*xangleshift[i]*np.arange(xx.size),dtype=np.complex64)*np.conj(x2))
    return (np.abs(y/len(x2))**2,xangleshift/(np.pi*2*interleav_len))

# obsolete
class no_delay_moving_average_ccc:
    def __init__(self,size):
        self.mavg = moving_average_ccc(size)
        self.out = array_with_hist([],size-1)

    def work(self,x):
        self.out.resize(x.size)
        self.out[-self.out.hist_len:-self.out.hist_len+x.size] = self.mavg.work(x)

# tested
class array_with_hist(object):# need to base it on object for negative slices
    def __init__(self,array,hist_len):
        self.hist_len = hist_len
        self.size = len(array)
        if type(array) is np.ndarray:
            self.array_h = np.append(np.zeros(hist_len,dtype=array.dtype),array)
        else:
            self.array_h = np.append(np.zeros(hist_len),array)
        self.dtype = array.dtype

    def __str__(self):
        return '[{}]'.format(', '.join(str(i) for i in self.array_h[0:self.size]))

    def capacity(self):
        return len(self.array_h)

    def reserve(self,siz):
        if siz+self.hist_len > self.capacity():
            diff = siz+self.hist_len-self.capacity()
            self.array_h = np.append(self.array_h,np.zeros(diff,dtype=self.array_h.dtype))

    # def __len__(self):
    #     return self.size+self.hist_len

    def __getitem__(self,idx):
        if type(idx) is slice:
            start = idx.start+self.hist_len if idx.start is not None else 0
            stop = idx.stop+self.hist_len if idx.stop is not None else self.size+self.hist_len
            # print stop,self.size+self.hist_len,start,idx
            assert stop<=self.size+self.hist_len and start>=0
            return self.array_h[start:stop:idx.step]
            # assert idx.stop <= self.size
            # start = idx.start+self.hist_len if idx.start <= self.size else idx.start-self.size
            # stop = idx.stop+self.hist_len if idx.stop <= self.size else idx.stop-self.size
            # print 'wololo2:',start,stop
            # return self.array_h[start:stop]
        assert idx<=self.size+self.hist_len
        return self.array_h[idx+self.hist_len]

    def data(self):
        return self.array_h[0:self.hist_len+self.size]

    # def __setitem__(self,idx,value):
    #     if type(idx) is slice:
    #         self.array_h[idx.start+self.hist_len:idx.stop+self.hist_len:idx.step] = value
    #     else:
    #         self.array_h[idx+self.hist_len] = value

    def advance(self):
        self.array_h[0:self.hist_len] = self.array_h[self.size:self.size+self.hist_len]

    def push(self,x):
        assert x.dtype==self.array_h.dtype
        self.advance()
        self.reserve(x.size)
        self.size = x.size
        self.array_h[self.hist_len:self.hist_len+len(x)] = x

# not tested
class offset_array_view(object):
    def __init__(self,array,offset):
        if type(array) is np.ndarray:
            self.array = array
            self.size = self.array.size-offset
            self.hist_len = offset
        elif type(array) is array_with_hist:
            self.array = array.array_h
            self.hist_len = array.hist_len+offset
            self.size = array.size-toffset
        assert self.size>=0

    def __getitem__(self,idx):
        if type(idx) is slice:
            start = idx.start+self.hist_len if idx.start is not None else None
            stop = idx.stop+self.hist_len if idx.stop is not None else None
            return self.array[start:stop:idx.step]
        return self.array[idx+self.hist_len]
def test1():
    mavg = moving_average_ccc(5)
    x = [1,1,1,1,1]

    y = mavg.work(x)
    assert len(y) == len(x)
    assert y[-1]==1

def test2():
    mavg = moving_average_ccc(6)
    x=range(10)

    y = mavg.work(x[0:5])
    y2 = mavg.work(x[5:10])
    yfinal = np.append(y,y2)

    assert len(yfinal)==len(x)
    assert yfinal[-1] == np.mean(range(4,10))

def test3():
    mavg = moving_average_ccc(10)
    filt = filter_ccc(np.ones(10)/10.0)
    x = range(20)

    y = mavg.work(x)
    y2 = filt.work(x)

    assert np.sum(np.abs(y-y2))<0.000001

if __name__=='__main__':
    test1()
    test2()
    test3()
