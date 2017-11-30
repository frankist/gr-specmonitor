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
import os
from matplotlib import colors
import pickle
from matplotlib.backends.backend_pdf import PdfPages
sys.path.append('../../')

from labeling_framework.utils import basic_algorithms as balg
from labeling_framework.labeling_tools import random_sequence
from labeling_framework.labeling_tools import preamble_utils

def unit_test1():
    """
    This test checks if the generated preamble params and frame params make sense
    """
    print 'UnitTest1:frame generation'

    guard_len=5
    awgn_len=50
    frame_period = 1000
    lvl2_seq_diff = random_sequence.maximum_length_sequence(7)
    lvl2_diff_len = len(lvl2_seq_diff)

    pparams = preamble_utils.generate_preamble_type2([5,61],lvl2_diff_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)

    # check if frame params make sense
    assert pparams.length()==pparams.preamble.size
    assert np.abs(np.mean(np.abs(pparams.pseq_list_norm[1])**2)-1)<1.0e-6
    assert np.array_equal(np.real(preamble_utils.get_schmidl_sequence(pparams.pseq_list_coef[0:-1])),lvl2_seq_diff)

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

    assert y.size == (num_sections*fparams.frame_period) # check if the size matches
    assert len(section_ranges)==num_sections             # check if section_ranges makes sense
    assert all((s[1]-s[0])==fparams.section_duration() for s in section_ranges)
    assert np.sum([np.sum(np.abs(y[s[0]:s[1]]-1)) for s in section_ranges])==0 # check if sections are equal to 1
    tmp = guard_len*2+pparams.length()
    assert np.sum([np.sum(np.abs(y[s[0]-tmp-awgn_len:s[0]-tmp])) for s in section_ranges])==0
    preamble = pparams.preamble
    assert np.sum([np.sum(np.abs(y[s[0]-tmp:s[0]-tmp+pparams.length()]-preamble)) for s in section_ranges])==0

def test2():
    """
    In this test we check if we are able to synchronize with one preamble after breaking the input signal into parts
    in the stream.
    """
    print 'test2: Test sync with one preamble when I break my input'

    guard_len=5
    awgn_len=75
    frame_period = 2000
    lvl2_seq_diff = random_sequence.maximum_length_sequence(13)
    lvl2_diff_len = len(lvl2_seq_diff)
    lvl2_len = lvl2_diff_len+1
    small_pseq_len = 13

    dc_offset = 1.5
    cfo = 0.42/small_pseq_len
    amp=1.5

    pparams = preamble_utils.generate_preamble_type2([small_pseq_len,61],lvl2_diff_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)
    sframer = preamble_utils.SignalFramer(fparams)
    thres = [0.12,0.09]

    xlen = fparams.section_duration()+guard_len*2
    x = (np.random.randn(xlen)+np.random.randn(xlen)*1j)*0.1/np.sqrt(2)
    y,section_ranges = sframer.frame_signal(x,1)
    y = preamble_utils.apply_cfo(y,cfo)*amp+dc_offset*np.exp(1j*np.random.rand()*2*np.pi)

    def test_partitioning(toffset,partition_part):
        pdetec = preamble_utils.PreambleDetectorType2(fparams,thres1=thres[0],thres2=thres[1])
        pdetec2 = preamble_utils.PreambleDetectorType2(fparams,thres1=thres[0],thres2=thres[1])
        assert pdetec.lvl2_len == lvl2_len
        assert np.array_equal(np.real(pdetec.lvl2_seq_diff),lvl2_seq_diff)# assert the diff is equal to the MLS

        y_with_offset = np.append(np.zeros(toffset,dtype=y.dtype),y)
        pdetec.work(y_with_offset)
        x_h = pdetec.x_h.data()
        xschmidl = pdetec.xschmidl_nodc.data()
        xschmidl_filt = pdetec.xschmidl_filt_nodc.data()
        xcorr_filt = pdetec.xcorr_filt_nodc.data()
        xcrossautocorr = pdetec.xcrossautocorr_nodc.data()
        # detector_transform_visualizations(pdetec,awgn_len,cfo)

        pdetec2.work(y_with_offset[0:partition_part])
        x_h2 = np.array(pdetec2.x_h.data())
        xschmidl2 = np.array(pdetec2.xschmidl_nodc.data())
        xschmidl_filt2 = np.array(pdetec2.xschmidl_filt_nodc.data())
        xcorr_filt2 = np.array(pdetec2.xcorr_filt_nodc.data())
        xcrossautocorr2 = np.array(pdetec2.xcrossautocorr_nodc.data())
        pdetec2.work(y_with_offset[partition_part::])
        # detector_transform_visualizations(pdetec2,None)
        x_h2 = np.append(x_h2,pdetec2.x_h[0::])
        xschmidl2 = np.append(xschmidl2,pdetec2.xschmidl_nodc[0::])
        xschmidl_filt2 = np.append(xschmidl_filt2,pdetec2.xschmidl_filt_nodc[0::])
        xcorr_filt2 = np.append(xcorr_filt2,pdetec2.xcorr_filt_nodc[0::])
        xcrossautocorr2 = np.array(pdetec2.xcrossautocorr_nodc[0::])

        assert pdetec2.nread == pdetec.nread
        tlast = pdetec.nread
        def assert_aligned(x,x2):
            siz = min(x.size,x2.size)
            assert np.max(np.abs(x[x.size-siz::]-x2[x2.size-siz::]))<1.0e-6
        assert_aligned(x_h2,x_h)
        assert_aligned(xschmidl2,xschmidl)
        assert_aligned(xschmidl_filt2,xschmidl_filt)
        assert_aligned(xcorr_filt2,xcorr_filt)

        # def plot_taligned(x,fmt='-'):
        #     t = np.arange(tlast-x.size,tlast)
        #     plt.plot(t,x,fmt)

        # plot_taligned(np.abs(xschmidl_filt),'r')
        # plot_taligned(np.abs(xschmidl_filt2),'rx')
        # plot_taligned(np.abs(xcorr_filt)**2,'b')
        # plot_taligned(np.abs(xcorr_filt2)**2,'bx')
        # t = np.arange(pdetec.nread-xcrossautocorr.size,pdetec.nread)
        # plt.plot(t,np.abs(xcrossautocorr),'x-')
        # t = np.arange(pdetec2.nread-xcrossautocorr2.size,pdetec2.nread)
        # plt.plot(t,np.abs(xcrossautocorr2),'.--')
        # plt.show()

        assert len(pdetec.peaks)==1 and len(pdetec2.peaks)==1
        p = pdetec2.peaks[0]
        assert p.tidx == fparams.awgn_len+toffset and pdetec.peaks[0].is_equal(p)
        assert p.awgn_mag2_nodc<0.000001
        assert np.abs(p.preamble_mag2-amp**2)<1.0e-6
        assert np.abs(p.cfo-cfo)<1.0e-4
        # print p.xcorr,amp**2
        # assert np.abs(p.xcorr-amp**2)<0.05
        assert p.xautocorr/amp**2>0.95
        # detector_transform_visualizations(pdetec)

        # print 'min idx:',preamble_utils.min_idx

    for toffset in range(0,y.size):
        for partition in [y.size/16,y.size/8,y.size/4,y.size/2,y.size*3/4]:
            test_partitioning(toffset,partition)

    # pdetec.work(y)

def test3():
    print 'test3: Test sync against SNR'
    np.random.seed(1)

    guard_len=5
    awgn_len=75
    frame_period = 1500
    lvl2_len = 13
    pseq_len = [13,61]

    dc_offset = 0.1
    cfo = -0.45/pseq_len[0]

    pparams = preamble_utils.generate_preamble_type2(pseq_len,lvl2_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)

    num_runs = 10
    SNRdB_range = range(-10,10)#[-7]
    FalseAlarmRate = np.zeros(len(SNRdB_range))
    Pdetec = np.zeros(len(SNRdB_range))
    for si,s in enumerate(SNRdB_range):
        amp = 10**(s/20.0)
        for r in range(num_runs):
            sframer = preamble_utils.SignalFramer(fparams)
            pdetec = preamble_utils.PreambleDetectorType2(fparams,thres1=0.08,thres2=0.04)

            xlen = fparams.section_duration()+guard_len*2
            x = (np.random.randn(xlen)+np.random.randn(xlen)*1j)*0.1/np.sqrt(2)
            y,section_ranges = sframer.frame_signal(x,1)
            y *= amp # the preamble has amplitude 1
            y = preamble_utils.apply_cfo(y,cfo)+dc_offset*np.exp(1j*np.random.rand()*2*np.pi)

            T = 1000
            toffset = 0#np.random.randint(0,T)
            yoffset = np.append(np.zeros(toffset,dtype=np.complex64),y)
            yoffset = np.append(yoffset,np.zeros(T-toffset,dtype=np.complex64))
            awgn = (np.random.randn(yoffset.size)+np.random.randn(yoffset.size)*1j)/np.sqrt(2)
            y_pwr = amp**2
            awgn_pwr = np.mean(np.abs(awgn)**2)
            yoffset += awgn
            # print 'AWGN pwr [dB]:',10*np.log10(awgn_pwr)
            # print 'actual SNRdB:',10*np.log10(y_pwr/awgn_pwr)
            # plt.plot(yoffset)
            # plt.show()

            pdetec.work(yoffset)

            test1 = False
            if len(pdetec.peaks)>0:
                max_el = np.argmax([np.abs(p.xcorr) for p in pdetec.peaks])
                test1 = pdetec.peaks[max_el].tidx == toffset+awgn_len
                print s,pdetec.peaks[0].tidx,toffset+awgn_len,test1
            num_fa = len(pdetec.peaks)-1 if test1 else len(pdetec.peaks)
            Pdetec[si] += test1
            FalseAlarmRate[si] += num_fa

            # print 'result:',test1
            # detector_transform_visualizations(pdetec)
    Pdetec /= float(num_runs)
    FalseAlarmRate /= float(num_runs)

    plt.plot(SNRdB_range,Pdetec,'x-')
    plt.plot(SNRdB_range,FalseAlarmRate,'o-')
    plt.show()

test4_base_file = os.path.expanduser('~/tmp/plot_data/test4_plot_2')#test4_plot')
test4_pkl_file = test4_base_file+'.pickle'

def test4():
    """
    In this test we plot the performance of the preamble param estimator for this SNR levels
    """
    print 'test4: Test sync against SNR'
    # np.random.seed(4)

    # preamble params
    guard_len=5
    awgn_len=200
    frame_period = 3000
    pseq_lvl2_len = len(random_sequence.maximum_length_sequence(13*8))#13*4
    pseq_len = [13,199]
    nrepeats0 = 1

    dc_offset = 2.0
    cfo = -0.45/pseq_len[0]

    pparams = preamble_utils.generate_preamble_type2(pseq_len,pseq_lvl2_len,nrepeats0)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_len,frame_period)

    num_runs = 500
    SNRdB_range = range(-20,15)
    FalseAlarmRate = np.zeros(len(SNRdB_range))
    Pdetec = np.zeros(len(SNRdB_range))
    amp_stats = []
    N = len(SNRdB_range)
    estim_stats = {'SNRdB':{'sum':np.zeros(N),'mse_sum':np.zeros(N)},
                   'detect_count':np.zeros(len(SNRdB_range)),
                   'amplitude':{'sum':np.zeros(N),'mse_sum':np.zeros(N)},
                   'awgn_mag2':{'sum':np.zeros(N),'mse_sum':np.zeros(N)},
                   'cfo':{'sum':np.zeros(N),'mse_sum':np.zeros(N)},
                   'dc_offset':{'abs_sum':np.zeros(N),'mse_sum':np.zeros(N)}}

    print 'preamble duration:',pparams.preamble_len,",",pseq_lvl2_len*pseq_len[0]
    for si,s in enumerate(SNRdB_range):
        amp_stats.append([0.0,0.0,0])
        amp = 10**(s/20.0)
        for r in range(num_runs):
            sframer = preamble_utils.SignalFramer(fparams)
            pdetec = preamble_utils.PreambleDetectorType2(fparams,pseq_len[0]*8,0.05,0.04)#0.08,0.04)

            xlen = int(fparams.frame_period*1.5)#fparams.section_duration()+guard_len*2
            # print 'xlen:',guard_len*2
            x = (np.random.randn(xlen)+np.random.randn(xlen)*1j)*0.1/np.sqrt(2)
            y,section_ranges = sframer.frame_signal(x,1)
            y *= amp # the preamble has amplitude 1
            y = preamble_utils.apply_cfo(y,cfo)

            T = 1000
            toffset = 0#np.random.randint(0,T-pparams.preamble_len+fparams.awgn_len)
            preamble_start = toffset+awgn_len
            yoffset = np.append(np.zeros(toffset,dtype=np.complex64),y)
            yoffset = np.append(yoffset,np.zeros(T-toffset,dtype=np.complex64))
            awgn = (np.random.randn(yoffset.size)+np.random.randn(yoffset.size)*1j)/np.sqrt(2)
            y_pwr = amp**2
            awgn_pwr = np.mean(np.abs(awgn)**2)
            yoffset += awgn
            yawgn_nodc_pwr = np.mean(np.abs(yoffset[preamble_start:preamble_start+fparams.preamble_params.length()])**2)
            dc_offset_with_phase = dc_offset*np.exp(1j*np.random.rand()*2*np.pi)
            yoffset += dc_offset_with_phase
            # print 'AWGN pwr [dB]:',10*np.log10(awgn_pwr)
            print 'actual SNRdB:',10*np.log10(y_pwr/awgn_pwr)
            # print 'amplitude:',yawgn_nodc_pwr
            # plt.plot(yoffset)
            # plt.show()

            pdetec.work(yoffset)

            test1 = False
            if len(pdetec.peaks)>0:
                print 'peak detected at SNRdB=',s
                max_el = np.argmax([np.abs(p.xcorr) for p in pdetec.peaks])
                test1 = np.abs(pdetec.peaks[max_el].tidx-(toffset+awgn_len))<2
                if test1:
                    p = pdetec.peaks[max_el]
                    amp_stats[si][0] += p.preamble_mag2
                    amp_stats[si][1] += (p.preamble_mag2-amp**2)**2
                    amp_stats[si][2] += 1
                    estim_stats['amplitude']['sum'][si] += p.preamble_mag2
                    estim_stats['amplitude']['mse_sum'][si] += np.abs(p.preamble_mag2-yawgn_nodc_pwr)**2#(10**(s/10.0)+1))**2
                    estim_stats['SNRdB']['sum'][si] += p.SNRdB()
                    estim_stats['SNRdB']['mse_sum'][si] += np.abs(p.SNRdB()-10*np.log10(y_pwr/awgn_pwr))**2
                    estim_stats['awgn_mag2']['sum'][si] += p.awgn_mag2_nodc
                    estim_stats['awgn_mag2']['mse_sum'][si] += (p.awgn_mag2_nodc-awgn_pwr)**2
                    estim_stats['dc_offset']['abs_sum'][si] += np.abs(p.dc_offset)
                    estim_stats['dc_offset']['mse_sum'][si] += np.abs(p.dc_offset-dc_offset_with_phase)**2
                    estim_stats['cfo']['sum'][si] += p.cfo
                    estim_stats['cfo']['mse_sum'][si] += np.abs(p.cfo-cfo)**2
                    estim_stats['detect_count'][si] += 1
                print s,pdetec.peaks[0].tidx,toffset+awgn_len,test1
            num_fa = len(pdetec.peaks)-1 if test1 else len(pdetec.peaks)
            Pdetec[si] += test1
            FalseAlarmRate[si] += num_fa
            # if test1 is False or num_fa>0:
            # detector_transform_visualizations(pdetec)
            # print 'result:',test1
    Pdetec /= float(num_runs)
    FalseAlarmRate /= float(num_runs)

    tostore = {'estim_stats':estim_stats,
               'Pdetec':Pdetec,'FalseAlarmRate':FalseAlarmRate,
               'SNRdB_range':SNRdB_range,'dc_offset':dc_offset, 'cfo':cfo}

    with open(test4_pkl_file,'wb') as f:
        pickle.dump(tostore,f)

# NOTE: Check Jupyter file for plots

def load_and_plot_test4():
    with open(test4_pkl_file,'r') as f:
        data = pickle.load(f)
        estim_stats = data['estim_stats']
        Pdetec = data['Pdetec']
        FalseAlarmRate = data['FalseAlarmRate']
        SNRdB_range = data['SNRdB_range']
        dc_offset = data['dc_offset']
        cfo = data['cfo']
        N = len(SNRdB_range)

        counts = np.array([max(estim_stats['detect_count'][i],1) for i in range(N)])
        preamble_amp_avg = estim_stats['amplitude']['sum']/counts
        preamble_amp_real = np.array([10**(s/10.0)+1 for s in SNRdB_range])

        fig, (ax0,ax1,ax2) = plt.subplots(nrows=3)
        ax0.plot(SNRdB_range,Pdetec,'x-')
        ax0.plot(SNRdB_range,FalseAlarmRate,'o-')

        ax1.plot(SNRdB_range,np.sqrt(estim_stats['amplitude']['mse_sum']/counts))
        ax1.plot(SNRdB_range,np.sqrt(estim_stats['SNRdB']['mse_sum']/counts))
        ax1.plot(SNRdB_range,np.sqrt(estim_stats['dc_offset']['mse_sum']/counts))
        ax1.plot(SNRdB_range,np.sqrt(estim_stats['awgn_mag2']['mse_sum']/counts),':')
        ax1.plot(SNRdB_range,np.sqrt(estim_stats['cfo']['mse_sum']/counts),':')
        ax1.set_ylabel('RMSE')
    
        ax2.plot(SNRdB_range,preamble_amp_avg-preamble_amp_real)
        ax2.plot(SNRdB_range,estim_stats['SNRdB']['sum']/counts-SNRdB_range)
        ax2.plot(SNRdB_range,estim_stats['dc_offset']['abs_sum']/counts-dc_offset,':')
        ax2.plot(SNRdB_range,estim_stats['awgn_mag2']['sum']/counts-1,'.-')
        ax2.plot(SNRdB_range,estim_stats['cfo']['sum']/counts-cfo)
        ax2.set_ylabel('bias')
        plt.show()

def detector_transform_visualizations(pdetec,maxautocorr=200,real_cfo=0):
    preamble_len = pdetec.params.length()
    L = pdetec.params.length()
    L0 = pdetec.pseq0_tot_len
    l0 = pdetec.pseq0.size
    l1 = pdetec.params.pseq_list_norm[1].size
    nout = pdetec.x_h.size
    hl = pdetec.x_h.hist_len
    barker_vec = pdetec.params.pseq_list_coef[0:-1]
    lvl2_len = len(barker_vec)
    barker_diff = preamble_utils.get_schmidl_sequence(barker_vec)
    # real_cfo = -0.45/l0
    # assert pdetec.xschmidl_filt_mag2_nodc.size==nout:
    print 'hist:',hl,'preamble len:',preamble_len,'barker:',len(barker_vec)
    assert L0==pdetec.delay_cum[0]+1

    # create x without dc
    x = pdetec.x_h[-pdetec.x_h.hist_len::]
    dc_mavg1 = balg.moving_average_no_hist(x,L0)
    dc_mavg2 = balg.moving_average_no_hist(x,L)
    dc_mavg3 = balg.moving_average_no_hist(x,pdetec.awgn_len)
    dc_mavg_l1 = balg.moving_average_no_hist(x,l1)
    x_no_dc = x[0:x.size-L0+1]-dc_mavg1
    x_no_dc2 = x[0:x.size-L+1]-dc_mavg2
    x_no_dc3 = x[pdetec.awgn_len-1:x.size]-dc_mavg3
    assert np.array_equal(pdetec.xdc_mavg_h[pdetec.delay_cum[0]::],dc_mavg1[hl::])
    assert np.array_equal(pdetec.xnodc_h[pdetec.delay_cum[0]::],x_no_dc[hl::])

    xmag2_mavg1 = balg.moving_average_no_hist(np.abs(x)**2,L0)
    xmag2_mavg2 = balg.moving_average_no_hist(np.abs(x)**2,L)
    xmag2_mavg3 = balg.moving_average_no_hist(np.abs(x)**2,pdetec.awgn_len)
    xmag2_mavg_no_dc = np.array([np.mean(np.abs(x[i:i+L0]-dc_mavg1[i])**2) for i in range(x_no_dc.size-L0+1)])
    xmag2_mavg_no_dc2 = np.array([np.mean(np.abs(x[i:i+L]-dc_mavg2[i])**2) for i in range(x_no_dc2.size-L+1)])
    xmag2_mavg_no_dc_l1 = np.array([np.mean(np.abs(x[i:i+l1]-dc_mavg_l1[i])**2) for i in range(x.size-l1+1)])

    # compute the schmidl&cox autocorrelation signal
    xschmidl = preamble_utils.compute_schmidl_cox_peak(x,l0)/l0
    xschmidl_no_dc = preamble_utils.compute_schmidl_cox_peak(x_no_dc,l0)/l0
    xschmidl_filt = preamble_utils.interleaved_crosscorrelate(xschmidl,np.array(barker_diff),l0)/len(barker_diff)
    xschmidl_filt_no_dc = preamble_utils.interleaved_crosscorrelate(xschmidl_no_dc,np.array(barker_diff),l0)/len(barker_diff)
    cfo_no_dc = preamble_utils.compute_schmidl_cox_cfo(xschmidl_filt_no_dc,l0)
    # cfo_no_dc_no_filt = balg.moving_average_no_hist(preamble_utils.compute_schmidl_cox_cfo(xschmidl_no_dc,l0),l0)
    if maxautocorr is not None:
        cfo = preamble_utils.compute_schmidl_cox_cfo(xschmidl_filt_no_dc[hl+maxautocorr],pdetec.pseq0.size)
        x_no_cfo = preamble_utils.compensate_cfo(x,cfo)
        cfo3 = balg.interleaved_zc_cfo_estimation(x[hl+maxautocorr::],pdetec.params.pseq_list_norm[0],lvl2_len)
    assert np.array_equal(xschmidl_no_dc[hl::],pdetec.xschmidl_nodc[pdetec.delay_cum[1]::])
    assert np.array_equal(xschmidl_filt_no_dc[hl::],pdetec.xschmidl_filt_nodc[pdetec.delay_cum[2]::])
    # plt.plot(xschmidl_no_dc[hl::])
    # plt.plot(pdetec.xschmidl_nodc[pdetec.delay_cum[1]::],':')
    # plt.show()
    # assert np.array_equal(np.abs(xschmidl_filt_no_dc[hl::]),pdetec.xschmidl_filt_mag2_nodc[pdetec.delay_cum[2]::])
    # cfo = -0.49/pdetec.params.pseq_list_norm[0].size

    # compute the crosscorrelation function
    xcorr0 = np.correlate(x_no_dc,pdetec.params.pseq_list_norm[0])/l0
    xcorr0_mavg = preamble_utils.interleaved_crosscorrelate(np.abs(xcorr0)**2,np.ones(lvl2_len),l0)/lvl2_len
    if maxautocorr is not None:
        xcorr1 = np.abs(np.correlate(preamble_utils.compensate_cfo(x_no_dc,cfo),pdetec.params.pseq_list_norm[1])/len(pdetec.params.pseq_list_norm[1]))**2
    xcrossauto = xcorr0_mavg[0:xschmidl_filt_no_dc.size]*np.abs(xschmidl_filt_no_dc[0:xcorr0_mavg.size])
    assert np.max(np.abs(np.abs(xcorr0[hl::])**2-pdetec.xcorr_nodc[pdetec.delay2_cum[1]::]))<1.0e-5
    assert np.max(np.abs(np.abs(xcorr0_mavg[hl::])-pdetec.xcorr_filt_nodc[pdetec.delay2_cum[2]::]))<1.0e-5
    assert np.max(np.abs(xcrossauto[hl::]-pdetec.xcrossautocorr_nodc[pdetec.delay2_cum[2]::]))<1.0e-5

    # attempts
    xcorr0_mavg2,xcfo0 = preamble_utils.interleaved_crosscorrelate_rotated(np.correlate(x,pdetec.params.pseq_list_norm[0])/l0,pdetec.lvl2_seq,l0)
    xcorr00 = np.abs(preamble_utils.interleaved_crosscorrelate(np.correlate(preamble_utils.compensate_cfo(x,xcfo0[hl+75]),pdetec.params.pseq_list_norm[0])/l0,pdetec.lvl2_seq,l0)/pdetec.lvl2_len)**2
    if maxautocorr is not None:
        print 'cfo:',cfo,real_cfo,xcfo0[75+hl],cfo3
    # xcorr0_mavg2 = np.abs(preamble_utils.interleaved_crosscorrelate(xcorr0,pdetec.lvl2_seq,l0)/pdetec.lvl2_len)**2#+np.abs(preamble_utils.interleaved_crosscorrelate(xcorr0[l0*4::],pdetec.lvl2_seq[4:6],l0)/2)**2#,np.ones(pdetec.lvl2_len-1),l0)/(pdetec.lvl2_len-1)
    def compute_partial_xcorr0(d,siz):
        return np.abs(preamble_utils.interleaved_crosscorrelate(xcorr0[d*l0::],pdetec.lvl2_seq[d:d+siz],l0)/siz)**2
    def func1(num,siz):
        assert num>1
        return np.mean([compute_partial_xcorr0(i,siz)[0:-(num-i)*l0] for i in range(num)],0)
    xcorr1_mavg2 = compute_partial_xcorr0(0,4)[0:-4*l0]+compute_partial_xcorr0(4,4)#func1(pdetec.lvl2_len-5,5)#compute_partial_xcorr0(0,5)[0:-l0]#+compute_partial_xcorr0(1,2)
    xcorr0_filt = np.abs(preamble_utils.interleaved_crosscorrelate(xcorr0,barker_vec,l0)/lvl2_len)**2
    # xcorr0_filt = np.abs(preamble_utils.interleaved_crosscorrelate(preamble_utils.compensate_cfo(xcorr0[0:cfo_no_dc.size],cfo_no_dc),np.ones(pdetec.lvl2_len),l0)/pdetec.lvl2_len)**2
    xcorr = np.correlate(x,pdetec.params.preamble)/L
    if maxautocorr is not None:
        xcorr_cfo_correct = np.correlate(preamble_utils.compensate_cfo(x,cfo),pdetec.params.preamble)/L
        xcorr_cfo_dc_correct = np.correlate(preamble_utils.compensate_cfo(x_no_dc2,cfo),pdetec.params.preamble)/L
        xcorr_cfo_dc_correct_alt = np.correlate(preamble_utils.compensate_cfo(x_no_dc3,cfo),pdetec.params.preamble)/L
        xcrossauto2 = xcorr1[L0:xschmidl_filt_no_dc.size+L0]*np.abs(xschmidl_filt_no_dc[0:xcorr1.size-L0])
        corrmax = max(np.max(np.abs(xcorr_cfo_correct)),np.max(np.abs(xcorr)))

    fig, (ax0,ax1) = plt.subplots(nrows=2)

    leg1 = []
    # ax0.plot(np.abs(x[hl::])**2,color=colors.cnames['silver'])
    # ax0.plot(xmag2_mavg1[hl::])
    # ax0.plot(np.abs(xschmidl[hl::]),':')
    # # ax0.plot(np.abs(pdetec.xschmidl[d1::]),':')
    # ax0.plot(np.abs(xschmidl_no_dc[hl::]),':')
    # ax0.plot(pdetec.xschmidl_filt_mag2[d2::])
    # ax0.plot(np.abs(xschmidl_filt[hl::]),'--')
    ax0.plot(np.abs(xcorr0_mavg[hl::]),'x:') ; leg1.append('Xcorr0^2 mavg')
    ax0.plot(np.abs(xschmidl_filt_no_dc[hl::]),'--') ; leg1.append('S&C mavg')
    # # ax0.plot(maxautocorr,pdetec.xschmidl_filt_mag2[pdetec.xschmidl_filt_delay+maxautocorr],'o')
    # ax0.plot(np.abs(xcorr[hl::])**2,'.',color=colors.cnames['silver'])
    # ax0.plot(np.abs(xcorr_cfo_correct[hl::])**2,'.-',color=colors.cnames['silver'])
    if maxautocorr is not None:
        ax0.plot(np.abs(xcorr_cfo_dc_correct[hl::])**2,'o--') ; leg1.append('Xcorr(preamble)')
        ax0.plot(np.abs(xcorr1[hl+L0::]),'d:') ; leg1.append('Xcorr(seq1)')
    ax0.plot(np.abs(xmag2_mavg_no_dc[hl::]),color=colors.cnames['limegreen']); leg1.append('mag2 mavg noDC')
    # ax0.plot(np.abs(xcorr0_filt[hl::]),'o--')
    # ax0.plot(np.abs(xcorr0_mavg2[hl::]),'d--')
    # ax0.plot(np.abs(xcorr00[hl::]),'d--')
    # ax0.plot(np.abs(xcorr1_mavg2[hl::]),'d--')
    # # ax0.plot(np.abs(xcorr0[hl::])**2,'x--')
    # # ax0.plot(np.abs(preamble_utils.compensate_cfo(xcorr0[0:cfo_no_dc.size],cfo_no_dc))**2,'x--')
    # # ax0.plot(preamble_utils.compute_schmidl_cox_cfo(preamble_utils.compensate_cfo(xcorr0[0:cfo_no_dc.size],cfo_no_dc),l0),'x--')
    # # ax0.plot(np.abs(pdetec.xschmidl_filt_nodc[L0+pdetec.xschmidl_filt_delay::]),'x')
    ax0.plot(np.sqrt(np.abs(xcrossauto[hl::])),'d-') ; leg1.append('S&C*Xcorr')
    # ax0.plot(np.abs(xcrossauto2[hl::]),'d-')

    # ax0.plot(np.abs(x_no_dc[hl::]),'o--')
    # ax0.plot(np.abs(dc_mavg1[hl::]),'.-')
    # ax0.plot(np.abs(pdetec.xdc_mavg_h[L0::]),'x--')
    ax0.plot(xmag2_mavg_no_dc[hl::],'--') ; leg1.append('new')

    # ax0.plot(preamble_utils.compute_schmidl_cox_cfo(pdetec.xschmidl_filt[pdetec.xschmidl_filt_delay::],pdetec.pseq0.size),'.')
    ax0.legend(leg1)#['|.|^2','MovAvg','autocorr','autocorr_dc_correct','autocorr_filt','autocorr_filt_dc_correct'])
    if maxautocorr is not None:
        print 'maxi:',np.argmax(np.abs(xcrossauto[hl::])),np.argmax(np.abs(xcorr1[hl+L0::])),np.argmax(np.abs(xcrossauto2[hl::]))

    def plot_norm(ax,x,xmag,fmt='-'):
        siz = min(x.size,xmag.size)
        ax.plot(x[0:siz]/xmag[0:siz],fmt)

    leg2 = []
    # # ax1.plot(pdetec.xschmidl_filt_mag2[d2::]/mavg_vec[0:nout-d2])
    # ax1.plot(np.abs(xschmidl_filt[hl::])/xmag2_mavg1[hl:xschmidl_filt.size],color=colors.cnames['silver'])
    # ax1.plot(np.abs(xcorr[hl:xmag2_mavg2.size])**2/xmag2_mavg2[hl::])
    # ax1.plot(np.abs(xcorr_cfo_correct[hl:xmag2_mavg2.size])**2/xmag2_mavg2[hl::])
    # ax1.plot(np.abs(xcorr_cfo_dc_correct[hl::])**2/xmag2_mavg_no_dc2[hl::],color=colors.cnames['tomato'],linewidth=2,linestyle=':',marker='o')
    # ax1.plot(np.abs(xcorr_cfo_dc_correct_alt[hl-pdetec.awgn_len:xmag2_mavg_no_dc2.size-pdetec.awgn_len])**2/xmag2_mavg_no_dc2[hl::],'x-',color=colors.cnames['silver'])
    plot_norm(ax1,np.abs(xschmidl_filt_no_dc[hl::]),xmag2_mavg_no_dc[hl::]) ; leg2.append('S&C filt')
    # ax1.plot(np.abs(xcorr0_filt[hl:xmag2_mavg_no_dc.size])/xmag2_mavg_no_dc[hl:xcorr0_filt.size],'.:')
    # ax1.plot(cfo_no_dc[hl::],'--')
    # ax1.plot(xcfo0[hl::],'--')
    # ax1.plot(np.abs(xcorr1_mavg2[hl:xmag2_mavg_no_dc.size])/3/xmag2_mavg_no_dc[hl::],'d:')
    plot_norm(ax1,np.abs(xcorr0_mavg[hl::]),xmag2_mavg_no_dc[hl::],'.:') ; leg2.append('Xcorr_mavg')
    # ax1.plot(np.abs(xcorr0_mavg[hl:xmag2_mavg_no_dc.size])/xmag2_mavg_no_dc[hl:xcorr0_mavg.size],'.:') ; leg2.append('Xcorr_mavg')
    if maxautocorr is not None:
        plot_norm(ax1,xcorr1[hl+L0::],xmag2_mavg_no_dc[hl::],'d:') ; leg2.append('Xcorr1')
        # ax1.plot(np.abs(xcorr1[hl+L0::])/xmag2_mavg_no_dc[hl:xcorr1.size-L0],'d:') ; leg2.append('Xcorr1')
    # # ax1.plot(cfo_no_dc_no_filt[hl::],'.--')
    # # ax1.legend(['autocorr_filt','xcorr_filt_no_cfo_correct','xcorr_filt','xcorr_filt_dc_correct','autocorr_dc_correct'])
    ax1.plot(np.sqrt(np.abs(xcrossauto[hl::]))/xmag2_mavg_no_dc[hl:xcrossauto.size],'--') ; leg2.append('S&C*Xcorr')
    ax1.legend(leg2)#['S&C_filt','Xcorr_mavg','Xcorr1','S&C*Xcorr'])
    plt.show()

if __name__=='__main__':
    unit_test1()
    # test2()
    # test3()
    test4()
    # load_and_plot_Pdetec_test4()
    # load_and_plot_test4()
    print 'Test completed sucessfully'
