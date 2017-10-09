#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2017 <+YOU OR YOUR COMPANY+>.
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
import sys
sys.path.append('../')
sys.path.append('../../utils/')
import preamble_utils
import zadoffchu

def test1():
    print 'Test frame generation'

    guard_len=5
    awgn_len=50
    frame_period = 1000

    pparams = preamble_utils.generate_preamble_type1([5,61],7)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)

    # check if frame params make sense
    assert pparams.length()==pparams.preamble.size
    assert fparams.section_duration() == (frame_period-4*guard_len-awgn_len-pparams.length())
    assert fparams.guarded_section_duration() == fparams.guarded_section_interval()[1]-fparams.guarded_section_interval()[0]
    assert fparams.section_duration()+2*guard_len == fparams.guarded_section_duration()
    assert fparams.section_interval()[1]-fparams.section_interval()[0]==fparams.section_duration()

    # check if the SignalFramer produces stuff that makes sense
    num_sections = 10
    x = np.ones(num_sections*fparams.section_duration()+guard_len*2,np.complex64)
    y,section_ranges = sframer.frame_signal(x,num_sections)

    # plt.plot(np.abs(y))
    # plt.show()

    assert y.size == (num_sections*fparams.frame_period)
    assert len(section_ranges)==num_sections
    assert all((s[1]-s[0])==fparams.section_duration() for s in section_ranges)
    assert np.sum([np.sum(np.abs(y[s[0]:s[1]]-1)) for s in section_ranges])==0 # check if sections are equal to 1
    tmp = guard_len*2+pparams.length()
    assert np.sum([np.sum(np.abs(y[s[0]-tmp-awgn_len:s[0]-tmp])) for s in section_ranges])==0
    preamble = pparams.preamble
    assert np.sum([np.sum(np.abs(y[s[0]-tmp:s[0]-tmp+pparams.length()]-preamble)) for s in section_ranges])==0

def test2():
    print 'Test sync with one preamble'

    guard_len=5
    awgn_len=50
    frame_period = 1000
    barker_len = 13

    cfo = 0.45/5
    print 'cfo:',cfo

    pparams = preamble_utils.generate_preamble_type1([5,61],barker_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)
    pdetec = preamble_utils.PreambleDetectorType1(fparams)
    pdetec2 = preamble_utils.PreambleDetectorType1(fparams)

    assert all([pdetec.barker_vec[i]==zadoffchu.barker_codes[barker_len][i] for i in range(barker_len)])

    x = np.ones(fparams.section_duration()+guard_len*2,dtype=np.complex64)
    y,section_ranges = sframer.frame_signal(x,1)
    y = preamble_utils.apply_cfo(y,cfo)

    # test if partitioning does not cause issues
    interr = y.size/8
    pdetec.work(y)
    x_h = pdetec.x_h[-pdetec.x_h.hist_len:pdetec.x_h.size]
    xschmidl = pdetec.xschmidl[-pdetec.xschmidl.hist_len:pdetec.xschmidl.size]
    xschmidl_filt = pdetec.xschmidl_filt[-pdetec.xschmidl_filt.hist_len:pdetec.xschmidl_filt.size]
    pdetec2.work(y[0:interr])
    x_h2 = np.array(pdetec2.x_h[-pdetec2.x_h.hist_len:pdetec2.x_h.size])
    xschmidl2 = np.array(pdetec2.xschmidl[-pdetec2.xschmidl.hist_len:pdetec2.xschmidl.size])
    xschmidl_filt2 = np.array(pdetec2.xschmidl_filt[-pdetec2.xschmidl_filt.hist_len:pdetec2.xschmidl_filt.size])
    pdetec2.work(y[interr:y.size])
    x_h2 = np.append(x_h2,pdetec2.x_h[0:pdetec2.x_h.size])
    xschmidl2 = np.append(xschmidl2,pdetec2.xschmidl[0:pdetec2.xschmidl.size])
    xschmidl_filt2 = np.append(xschmidl_filt2,pdetec2.xschmidl_filt[0:pdetec2.xschmidl_filt.size])
    assert np.mean(np.abs(x_h2-x_h))<0.0001
    assert np.mean(np.abs(xschmidl2-xschmidl))<0.0001
    # plt.plot(xschmidl_filt)
    # plt.plot(xschmidl_filt2,':')
    # plt.show()
    assert np.mean(np.abs(xschmidl_filt2-xschmidl_filt))<0.0001

    pdetec.work(y)

    # plt.plot(np.abs(pdetec.x_h))
    # plt.plot(np.abs(pdetec.xmag2_h))
    # plt.plot(np.abs(pdetec.xcorrsum),'x')
    # plt.plot(np.abs(pdetec.xschmidl_filt))
    # plt.plot(np.abs(pdetec.xcorr_filt),':')
    # plt.show()


if __name__=='__main__':
    #test1()
    test2()
    print 'Test completed sucessfully'
