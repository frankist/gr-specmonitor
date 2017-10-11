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
