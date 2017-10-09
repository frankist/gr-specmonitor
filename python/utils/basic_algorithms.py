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
