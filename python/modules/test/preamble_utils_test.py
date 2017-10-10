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
from matplotlib import colors

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
    awgn_len=75
    frame_period = 1000
    barker_len = 13
    small_pseq_len = 12

    dc_offset = 1.5
    cfo = 0.42/small_pseq_len
    amp=1.5

    pparams = preamble_utils.generate_preamble_type1([small_pseq_len,61],barker_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)


    xlen = fparams.section_duration()+guard_len*2
    x = (np.random.randn(xlen)+np.random.randn(xlen)*1j)*0.1/np.sqrt(2)
    y,section_ranges = sframer.frame_signal(x,1)
    y = preamble_utils.apply_cfo(y,cfo)*amp+dc_offset*np.exp(1j*np.random.rand()*2*np.pi)

    def test_partitioning(toffset,partition_part):
        pdetec = preamble_utils.PreambleDetectorType1(fparams)
        pdetec2 = preamble_utils.PreambleDetectorType1(fparams)
        assert all([pdetec.barker_vec[i]==zadoffchu.barker_codes[barker_len][i] for i in range(barker_len)])

        y_with_offset = np.append(np.zeros(toffset,dtype=y.dtype),y)
        pdetec.work(y_with_offset)
        x_h = pdetec.x_h.data()
        xschmidl = pdetec.xschmidl_nodc.data()
        xschmidl_filt = pdetec.xschmidl_filt_nodc.data()

        pdetec2.work(y_with_offset[0:partition_part])
        x_h2 = np.array(pdetec2.x_h.data())
        xschmidl2 = np.array(pdetec2.xschmidl_nodc.data())
        xschmidl_filt2 = np.array(pdetec2.xschmidl_filt_nodc.data())
        pdetec2.work(y_with_offset[partition_part::])
        x_h2 = np.append(x_h2,pdetec2.x_h[0::])
        xschmidl2 = np.append(xschmidl2,pdetec2.xschmidl_nodc[0::])
        xschmidl_filt2 = np.append(xschmidl_filt2,pdetec2.xschmidl_filt_nodc[0::])

        # detector_transform_visualizations(pdetec)
        
        assert np.mean(np.abs(x_h2-x_h))<0.0001
        assert np.mean(np.abs(xschmidl2-xschmidl))<0.0001
        # plt.plot(xschmidl_filt)
        # plt.plot(xschmidl_filt2,':')
        # plt.show()
        assert np.mean(np.abs(xschmidl_filt2-xschmidl_filt))<0.0001
        assert len(pdetec.peaks)==1 and len(pdetec2.peaks)==1
        p = pdetec2.peaks[0]
        assert p.tidx == fparams.awgn_len+toffset and pdetec.peaks[0].is_equal(p)
        assert p.awgn_mag2_nodc<0.000001
        assert np.abs(p.preamble_mag2-amp**2)<0.000001
        assert np.abs(p.cfo-cfo)<0.0001
        assert np.abs(p.xcorr-amp**2)<0.05
        assert p.xautocorr/amp**2>0.95

        # print 'min idx:',preamble_utils.min_idx

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
    preamble_len = pdetec.params.length()
    L = pdetec.params.length()
    L0 = pdetec.pseq0_tot_len
    l0 = pdetec.pseq0.size
    nout = pdetec.x_h.size
    hl = pdetec.x_h.hist_len
    assert pdetec.xschmidl_filt_mag2_nodc.size==nout

    # create x without dc
    x = pdetec.x_h[-pdetec.x_h.hist_len::]
    dc_vec = np.array([np.mean(pdetec.x_h[i:i+L0]) for i in range(pdetec.x_h.size-L0+1)])
    dc_vec2 = np.array([np.mean(pdetec.x_h[i:i+L]) for i in range(pdetec.x_h.size-L+1)])
    dc_mavg1 = np.array([np.mean(x[i:i+L0]) for i in range(x.size-L0)])
    dc_mavg2 = np.array([np.mean(x[i:i+L]) for i in range(x.size-L)])
    dc_mavg3 = np.array([np.mean(x[i:i+pdetec.awgn_len]) for i in range(x.size-pdetec.awgn_len)])
    x_no_dc = x[0:x.size-L0]-dc_mavg1
    x_no_dc2 = x[0:x.size-L]-dc_mavg2
    x_no_dc3 = x[pdetec.awgn_len:x.size]-dc_mavg3
    assert np.array_equal(pdetec.x_h[0::],x[hl::])
    assert np.array_equal(x_no_dc[hl::],pdetec.xnodc_h[L0::])

    mag2_mavg1 = np.array([np.mean(np.abs(x[i:i+L0])**2) for i in range(nout-L0+1)])
    mag2_mavg2 = np.array([np.mean(np.abs(x[i:i+L])**2) for i in range(nout-L+1)])
    xmag2_mavg_no_dc = np.array([np.mean(np.abs(x[i:i+L0]-dc_mavg1[i])**2) for i in range(x_no_dc.size-L0+1)])
    xmag2_mavg_no_dc2 = np.array([np.mean(np.abs(x[i:i+L]-dc_mavg2[i])**2) for i in range(x_no_dc2.size-L+1)])

    # compute the schmidl&cox autocorrelation signal
    xschmidl = preamble_utils.compute_schmidl_cox_peak(x,l0)/l0
    xschmidl_no_dc = preamble_utils.compute_schmidl_cox_peak(x_no_dc,l0)/l0
    xschmidl_filt = preamble_utils.interleaved_crosscorrelate(xschmidl,pdetec.barker_diff,l0)/len(pdetec.barker_diff)
    xschmidl_filt_no_dc = preamble_utils.interleaved_crosscorrelate(xschmidl_no_dc,pdetec.barker_diff,l0)/len(pdetec.barker_diff)
    maxautocorr = np.argmax(np.abs(xschmidl_filt[hl::]))
    cfo = preamble_utils.compute_schmidl_cox_cfo(pdetec.xschmidl_filt_nodc[pdetec.delay_cum[2]+maxautocorr],pdetec.pseq0.size)
    assert np.array_equal(xschmidl_no_dc[hl::],pdetec.xschmidl_nodc[pdetec.delay_cum[1]::])
    assert np.array_equal(xschmidl_filt_no_dc[hl::],pdetec.xschmidl_filt_nodc[pdetec.delay_cum[2]::])
    assert np.array_equal(np.abs(xschmidl_filt_no_dc[hl::]),pdetec.xschmidl_filt_mag2_nodc[pdetec.delay_cum[2]::])

    # compute the crosscorrelation function
    xcorr = np.correlate(x,pdetec.params.preamble)/L
    xcorr_cfo_correct = np.correlate(preamble_utils.compensate_cfo(x,cfo),pdetec.params.preamble)/L
    xcorr_cfo_dc_correct = np.correlate(preamble_utils.compensate_cfo(x_no_dc2,cfo),pdetec.params.preamble)/L
    xcorr_cfo_dc_correct_alt = np.correlate(preamble_utils.compensate_cfo(x_no_dc3,cfo),pdetec.params.preamble)/L
    corrmax = max(np.max(np.abs(xcorr_cfo_correct)),np.max(np.abs(xcorr)))

    fig, (ax0,ax1) = plt.subplots(nrows=2)

    ax0.plot(np.abs(x[hl::])**2,color=colors.cnames['silver'])
    ax0.plot(mag2_mavg1[hl::])
    ax0.plot(np.abs(xschmidl[hl::]),':')
    # ax0.plot(np.abs(pdetec.xschmidl[d1::]),':')
    ax0.plot(np.abs(xschmidl_no_dc[hl::]),':')
    # ax0.plot(pdetec.xschmidl_filt_mag2[d2::])
    ax0.plot(np.abs(xschmidl_filt[hl::]))
    ax0.plot(np.abs(xschmidl_filt_no_dc[hl::]),'--')
    # ax0.plot(maxautocorr,pdetec.xschmidl_filt_mag2[pdetec.xschmidl_filt_delay+maxautocorr],'o')
    ax0.plot(np.abs(xcorr[hl::])**2,'.')
    ax0.plot(np.abs(xcorr_cfo_correct[hl::])**2,'.-')
    ax0.plot(np.abs(xcorr_cfo_dc_correct[hl::])**2,'o--')
    ax0.plot(np.real(xmag2_mavg_no_dc[hl::]),color=colors.cnames['limegreen'])
    # ax0.plot(np.abs(pdetec.xschmidl_filt_nodc[L0+pdetec.xschmidl_filt_delay::]),'x')

    # ax0.plot(np.abs(x_no_dc[hl::]),'o--')
    # ax0.plot(np.abs(dc_mavg1[hl::]),'.-')
    # ax0.plot(np.abs(pdetec.xdc_mavg_h[L0::]),'x--')

    # ax0.plot(preamble_utils.compute_schmidl_cox_cfo(pdetec.xschmidl_filt[pdetec.xschmidl_filt_delay::],pdetec.pseq0.size),'.')
    ax0.legend(['|.|^2','MovAvg','autocorr','autocorr_dc_correct','autocorr_filt','autocorr_filt_dc_correct'])

    # ax1.plot(pdetec.xschmidl_filt_mag2[d2::]/mavg_vec[0:nout-d2])
    ax1.plot(np.abs(xschmidl_filt[hl:mag2_mavg1.size])/mag2_mavg1[hl::])
    ax1.plot(np.abs(xcorr[hl:mag2_mavg2.size])**2/mag2_mavg2[hl::])
    ax1.plot(np.abs(xcorr_cfo_correct[hl:mag2_mavg2.size])**2/mag2_mavg2[hl::])
    ax1.plot(np.abs(xcorr_cfo_dc_correct[hl::])**2/xmag2_mavg_no_dc2[hl::],color=colors.cnames['tomato'],linewidth=2,linestyle=':',marker='.')
    ax1.plot(np.abs(xcorr_cfo_dc_correct_alt[hl-pdetec.awgn_len:xmag2_mavg_no_dc2.size-pdetec.awgn_len])**2/xmag2_mavg_no_dc2[hl::],'x-')
    ax1.plot(np.abs(xschmidl_filt_no_dc[hl::])/xmag2_mavg_no_dc[hl:xschmidl_filt_no_dc.size])
    ax1.legend(['autocorr_filt','xcorr_filt_no_cfo_correct','xcorr_filt','xcorr_filt_dc_correct','autocorr_dc_correct'])
    plt.show()

if __name__=='__main__':
    #test1()
    test2()
    print 'Test completed sucessfully'
