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
    small_pseq_len = 5

    cfo = 0.45/small_pseq_len
    amp=1.4

    pparams = preamble_utils.generate_preamble_type1([small_pseq_len,61],barker_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)


    x = np.ones(fparams.section_duration()+guard_len*2,dtype=np.complex64)
    y,section_ranges = sframer.frame_signal(x,1)
    y = preamble_utils.apply_cfo(y,cfo)*amp

    def test_partitioning(toffset,partition_part):
        pdetec = preamble_utils.PreambleDetectorType1(fparams)
        pdetec2 = preamble_utils.PreambleDetectorType1(fparams)
        assert all([pdetec.barker_vec[i]==zadoffchu.barker_codes[barker_len][i] for i in range(barker_len)])

        y_with_offset = np.append(np.zeros(toffset,dtype=y.dtype),y)
        pdetec.work(y_with_offset)
        x_h = pdetec.x_h[-pdetec.x_h.hist_len:pdetec.x_h.size]
        xschmidl = pdetec.xschmidl[-pdetec.xschmidl.hist_len:pdetec.xschmidl.size]
        xschmidl_filt = pdetec.xschmidl_filt[-pdetec.xschmidl_filt.hist_len:pdetec.xschmidl_filt.size]

        pdetec2.work(y_with_offset[0:partition_part])
        x_h2 = np.array(pdetec2.x_h[-pdetec2.x_h.hist_len:pdetec2.x_h.size])
        xschmidl2 = np.array(pdetec2.xschmidl[-pdetec2.xschmidl.hist_len:pdetec2.xschmidl.size])
        xschmidl_filt2 = np.array(pdetec2.xschmidl_filt[-pdetec2.xschmidl_filt.hist_len:pdetec2.xschmidl_filt.size])
        pdetec2.work(y_with_offset[partition_part:y_with_offset.size])
        x_h2 = np.append(x_h2,pdetec2.x_h[0:pdetec2.x_h.size])
        xschmidl2 = np.append(xschmidl2,pdetec2.xschmidl[0:pdetec2.xschmidl.size])
        xschmidl_filt2 = np.append(xschmidl_filt2,pdetec2.xschmidl_filt[0:pdetec2.xschmidl_filt.size])

        detector_transform_visualizations(pdetec)
        
        assert np.mean(np.abs(x_h2-x_h))<0.0001
        assert np.mean(np.abs(xschmidl2-xschmidl))<0.0001
        # plt.plot(xschmidl_filt)
        # plt.plot(xschmidl_filt2,':')
        # plt.show()
        assert np.mean(np.abs(xschmidl_filt2-xschmidl_filt))<0.0001
        assert len(pdetec.peaks)==1 and len(pdetec2.peaks)==1
        p = pdetec2.peaks[0]
        assert p.tidx == fparams.awgn_len+toffset and pdetec.peaks[0].is_equal(p)
        assert p.awgn_mag2==0.0
        assert p.preamble_mag2==1.0
        assert np.abs(p.cfo-cfo)<0.0001
        assert np.abs(p.xcorr-1.0)<0.0001
        assert np.abs(p.xautocorr-1.0)<0.0001


    for toffset in range(0,y.size):
        for partition in [y.size/16,y.size/8,y.size/4,y.size/2,y.size*3/4]:
            test_partitioning(toffset,partition)
    
    # pdetec.work(y)

    # plt.plot(np.abs(pdetec.x_h))
    # plt.plot(np.abs(pdetec.xmag2_h))
    # plt.plot(np.abs(pdetec.xcorrsum),'x')
    # plt.plot(np.abs(pdetec.xschmidl_filt))
    # plt.plot(np.abs(pdetec.xcorr_filt),':')
    # plt.show()


def detector_transform_visualizations(pdetec):
    nout = pdetec.x_h.size
    plt.plot(np.abs(pdetec.x_h[0::])**2)
    plt.plot([np.mean(pdetec.xmag2_h[i:i+pdetec.pseq0_tot_len]) for i in range(pdetec.xmag2_h.size-pdetec.pseq0_tot_len)])#moving avg
    plt.plot(np.abs(pdetec.xschmidl[pdetec.xschmidl_delay::]))
    plt.plot(pdetec.xschmidl_filt_mag2[pdetec.xschmidl_filt_delay::])
    plt.plot(preamble_utils.compute_schmidl_cox_cfo(pdetec.xschmidl_filt[pdetec.xschmidl_filt_delay::],pdetec.pseq0.size),'o')
    maxautocorr = np.argmax(pdetec.xschmidl_filt_mag2[pdetec.xschmidl_filt_delay::])
    plt.plot(maxautocorr,pdetec.xschmidl_filt_mag2[pdetec.xschmidl_filt_delay+maxautocorr],'x')
    cfo = preamble_utils.compute_schmidl_cox_cfo(pdetec.xschmidl_filt[pdetec.xschmidl_filt_delay+maxautocorr],pdetec.pseq0.size)
    print maxautocorr,cfo
    xcorr = np.correlate(pdetec.x_h[0::],pdetec.params.preamble)
    xcorr_cfo_corrected = np.correlate(preamble_utils.compensate_cfo(pdetec.x_h[0::],cfo),pdetec.params.preamble)
    corrmax = max(np.max(np.abs(xcorr_cfo_corrected)),np.max(np.abs(xcorr)))
    plt.plot(np.abs(xcorr)/corrmax,':')
    plt.plot(np.abs(xcorr_cfo_corrected)/corrmax,':')
    plt.show()

if __name__=='__main__':
    #test1()
    test2()
    print 'Test completed sucessfully'
