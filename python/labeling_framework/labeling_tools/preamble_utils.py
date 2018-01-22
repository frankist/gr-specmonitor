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
import sys
import os
import matplotlib.pyplot as plt

from ..utils.basic_algorithms import *
from ..utils.array_view import *
import random_sequence
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class preamble_params:
    def __init__(self, pseq_list, pseq_list_seq, pseq_list_coef = None):
        self.pseq_list = pseq_list
        # TODO: Make the amplitude consistent
        self.pseq_list_norm = self.compute_normalized_pseq_list()
        self.pseq_list_seq = pseq_list_seq
        self.pseq_list_coef = pseq_list_coef
        if self.pseq_list_coef is None:
            self.pseq_list_coef = np.ones(len(self.pseq_list_seq))
        self.preamble_len = np.sum([self.pseq_list[i].size for i in pseq_list_seq])
        self.preamble = self.generate_preamble()

    def compute_normalized_pseq_list(self):
        pnorm = []
        for i in range(len(self.pseq_list)):
            pnorm.append(self.pseq_list[i] / np.sqrt(np.mean(np.abs(self.pseq_list[i])**2)))
        return pnorm

    def generate_preamble(self):
        y = np.zeros(self.preamble_len,dtype='complex64')
        n=0
        for i,p in enumerate(self.pseq_list_seq):
            y[n:n+self.pseq_list[p].size] = self.pseq_list[p] * self.pseq_list_coef[i]
            n = n+self.pseq_list[p].size
        y /= np.sqrt(np.mean(np.abs(y)**2))
        return y

    def length(self):
        return self.preamble.size

# example: params -> [5,11], 4 --> [zc(5) zc(5) -zc(5) zc(5) zc(11)]
# def generate_preamble_type1(pseq_len_list, barker_len):
#     assert len(pseq_len_list)==2
#     pseq_list = [random_sequence.zadoffchu_sequence(p,1,0) for p in pseq_len_list]
#     # pseq_dc_list = [np.mean(pseq_list[i]) for i in range(len(pseq_len_list))]
#     # pseq_list = [pseq_list[i]-pseq_dc_list[i] for i in range(len(pseq_len_list))]
#     pseq_list_coef = random_sequence.barker_code[barker_len]+[1]
#     pseq_len_seq = [0]*barker_len+[1]
#     return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

def generate_preamble_type2(pseq_len_list, pseq_lvl2_len, num_repeats=1):
    assert len(pseq_len_list)==2
    pseq_list = [random_sequence.zadoffchu_noDC_sequence(p,1,0) for p in pseq_len_list]
    lvl2_code = random_sequence.maximum_length_sequence(pseq_lvl2_len)
    # barkercode = zadoffchu.barker_codes[barker_len]
    lvl2_many = np.array([])
    for i in range(num_repeats):
        lvl2_many = np.append(lvl2_many,lvl2_code)
    pseq_list_coef = set_schmidl_sequence(lvl2_many)
    pseq_list_coef = np.append(pseq_list_coef,1)
    pseq_len_seq = [0]*(pseq_lvl2_len*num_repeats+1)+[1]
    return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

def get_schmidl_sequence(crosscorr_seq):
    schmidl_seq = np.ones(len(crosscorr_seq)-1,dtype=np.complex64)
    for i in range(len(schmidl_seq)):
        # schmidl_seq[i] = np.exp(1j*np.angle(crosscorr_seq[i+1]*crosscorr_seq[i]))
        schmidl_seq[i] = np.exp(1j*(np.angle(crosscorr_seq[i+1])-np.angle(crosscorr_seq[i])))
    return schmidl_seq

def set_schmidl_sequence(autocorr_seq):
    crosscorr_seq = np.ones(len(autocorr_seq)+1,dtype=np.complex64)
    for i in range(len(autocorr_seq)):
        crosscorr_seq[i+1] = np.exp(1j*(np.angle(crosscorr_seq[i])+np.angle(autocorr_seq[i])))
        # crosscorr_seq[i+1] = np.exp(1j*(np.angle(crosscorr_seq[i]*autocorr_seq[i])))
    # assert np.array_equal(np.real(get_schmidl_sequence(crosscorr_seq)),autocorr_seq)
    return crosscorr_seq

# Frame structure: [awgn_len | preamble | guard0 | guard1 | section | guard2 | guard3]
# guard0 and guard3 are zeros.
class frame_params:
    def __init__(self,pparams,guard_len,awgn_len,frame_period):
        self.preamble_params = pparams
        self.guard_len = guard_len
        self.awgn_len = awgn_len
        self.frame_period = frame_period
        assert self.section_duration()>0

    def section_duration(self):
        return self.frame_period - (self.preamble_params.length()+self.guard_len*4+self.awgn_len)

    def guarded_section_duration(self):
        return self.frame_period - (self.preamble_params.length()+self.guard_len*2+self.awgn_len)

    def guarded_section_interval(self):
        return (self.awgn_len+self.preamble_params.length()+self.guard_len,self.frame_period-self.guard_len)

    def section_interval(self):
        return (self.awgn_len+self.preamble_params.length()+self.guard_len*2,self.frame_period-self.guard_len*2)

    def preamble_interval(self):
        return (self.awgn_len,self.awgn_len+self.preamble_params.length())

    @staticmethod
    def compute_frame_period(section_size,preamble_len,guard_len,awgn_len):
        return section_size + 4*guard_len + awgn_len + preamble_len

# [0|1,2,3,4|5],[4|5,6,7,8|9],...
class SignalFramer:
    def __init__(self,fparams):
        self.frame_params = fparams

    def generate_framed_section(self,xsection):
        assert xsection.size == self.frame_params.guarded_section_duration()
        framed_section = np.zeros(self.frame_params.frame_period,dtype=np.complex64)
        t = self.frame_params.preamble_interval()
        framed_section[t[0]:t[1]] = self.frame_params.preamble_params.preamble
        t = self.frame_params.guarded_section_interval()
        framed_section[t[0]:t[1]] = xsection
        return framed_section

    def get_framed_section_ranges(self,num_sections):
        T = self.frame_params.frame_period
        I = self.frame_params.section_interval()
        return [(i*T+I[0],i*T+I[1]) for i in range(num_sections)]

    # frame: [[0]*awgn_len | preamble | [0]*guard_len | [x]*(section_size+2*guard_len) | [0]*guard_len]
    def frame_signal(self,x,num_sections):
        nread = self.expected_nread_samples(num_sections)
        nwritten = self.frame_params.frame_period*num_sections
        assert x.size>=nread

        T = self.frame_params.frame_period
        T0 = self.frame_params.section_duration()
        framed_signal = np.zeros(nwritten,np.complex64)
        for i in range(num_sections):
            framed_signal[i*T:(i+1)*T] = self.generate_framed_section(x[i*T0:(i+1)*T0+2*self.frame_params.guard_len])
        section_ranges = self.get_framed_section_ranges(num_sections)

        return (framed_signal,section_ranges)

    def expected_nread_samples(self,num_sections):
        return self.frame_params.section_duration()*num_sections+2*self.frame_params.guard_len

class tracked_peak:
    def __init__(self, tidx, xcorr_peak, xautocorr, cfo, xmag2, awgn_estim_nodc, dc_offset):
        self.tidx = tidx
        self.xcorr = xcorr_peak
        self.xautocorr = xautocorr
        self.cfo = cfo
        self.preamble_mag2 = xmag2
        self.awgn_mag2_nodc = awgn_estim_nodc
        self.dc_offset = dc_offset

    def __str__(self):
        return '[{}, {}, {}, {}, {}, {}, {}]'.format(self.tidx,self.xcorr,self.xautocorr,self.cfo,self.preamble_mag2,self.awgn_mag2_nodc,self.dc_offset)

    def is_equal(self,t):
        return self.tidx==t.tidx and self.xcorr==t.xcorr and self.xautocorr==t.xautocorr and self.cfo==t.cfo and self.preamble_mag2==t.preamble_mag2 and self.awgn_mag2_nodc==t.awgn_mag2_nodc and self.dc_offset==t.dc_offset

    def snr(self):
        return (self.preamble_mag2-self.awgn_mag2_nodc)/self.awgn_mag2_nodc if self.preamble_mag2>=self.awgn_mag2_nodc else 0

    def SNRdB(self):
        snr_val = self.snr()
        if snr_val>0:
            return 10*np.log10(snr_val)
        return -np.inf

class PreambleDetectorType2:
    def __init__(self, fparams, autocorr_margin=None, thres1=0.08, thres2=0.04):#params, awgn_len):
        self.frame_params = fparams
        self.thres1 = thres1
        self.thres2 = thres2

        # derived
        self.params = self.frame_params.preamble_params
        self.L = self.params.preamble_len
        self.lvl2_seq = self.params.pseq_list_coef[0:-1]
        self.lvl2_len = len(self.lvl2_seq)
        self.lvl2_seq_diff = get_schmidl_sequence(self.lvl2_seq)
        self.pseq0 = self.params.pseq_list_norm[0]
        self.l0 = self.pseq0.size
        self.l1 = self.params.pseq_list_norm[1].size
        self.pseq0_tot_len = self.l0*self.lvl2_len
        self.L0 = self.pseq0_tot_len
        self.awgn_len = self.frame_params.awgn_len
        self.__max_margin__ = autocorr_margin if autocorr_margin is not None else self.pseq0_tot_len
        assert isinstance(self.__max_margin__,int)

        # object state variables
        self.nread = 0
        self.peaks = []

        # internal operation variables
        self.margin = 4#16
        self.hist_len = self.awgn_len + self.L
        self.delay = [self.pseq0_tot_len-1, self.l0*2-1, len(self.lvl2_seq_diff)*self.l0-1]
        self.delay2 = [self.delay[0], self.l0-1,self.lvl2_len*self.l0-1]
        self.delay_cum = np.cumsum(self.delay)
        self.delay2_cum = np.cumsum(self.delay2)
        self.hist_len2 = self.delay_cum[2]+self.L+self.awgn_len+2*self.margin

        # NOTE: we look back in time by self.delay_cum[2] to find peaks
        self.x_h = array_with_hist(np.array([],dtype=np.complex64),max(self.delay_cum[2],self.L0)) #self.hist_len2)
        self.xdc_mavg_h = array_with_hist(np.array([],dtype=np.complex64),self.delay_cum[2]-self.L0)
        self.xnodc_h = array_with_hist(np.array([],dtype=np.complex64),self.L0+self.delay_cum[0]+self.margin+self.l1)#self.hist_len2)
        self.xschmidl_nodc = array_with_hist(np.array([],dtype=np.complex64),self.L0)#self.hist_len)
        self.xschmidl_filt_nodc = np.array([],dtype=np.complex64)#array_with_hist(np.array([],dtype=np.complex64),0)#self.__max_margin__)
        self.xcorr_nodc = array_with_hist(np.array([],dtype=np.float32),self.L0)
        self.xcorr_filt_nodc = np.array([],dtype=np.float32)#self.__max_margin__+self.lvl2_len*self.pseq0.size)
        self.Ldiff = max(self.l1-self.__max_margin__,0) # this guarantees that the peak1 fits in window
        self.xcrossautocorr_nodc = array_with_hist(np.array([],dtype=np.float32),self.__max_margin__+self.Ldiff)
        self.local_max_finder_h = SlidingWindowMax_hist(self.__max_margin__)

    def find_crosscorr_peak(self,tpeak): # this is for high precision time sync
        # compensate CFO
        cfo = compute_schmidl_cox_cfo(self.xschmidl_filt_nodc[tpeak+self.delay_cum[2]],self.pseq0.size)
        toffset = self.L0+self.delay_cum[0]
        pseq = self.params.pseq_list_norm[1]#self.params.preamble
        plen = len(pseq)
        twin = (tpeak-self.margin+toffset,tpeak+plen+self.margin+toffset)

        y = compensate_cfo(self.xnodc_h[twin[0]:twin[1]],cfo)
        ycorr = np.correlate(y,pseq)
        maxi = np.argmax(np.abs(ycorr))
        ymag2 = np.mean(np.abs(self.xnodc_h[twin[0]+maxi:twin[0]+maxi+self.l1])**2)
        xcorr = np.abs(ycorr[maxi]/plen)**2

        return (tpeak,xcorr,cfo,ymag2)

    def work(self,x):
        l0 = self.pseq0.size
        L0 = self.pseq0_tot_len
        L = self.params.length()
        # print 'window:',self.nread,self.nread+x.size
        self.x_h.push(x) # [hist | x]
        self.xdc_mavg_h.push(moving_average_with_hist(self.x_h,L0)) # delay=delay_cum[0]=L0-1
        self.xnodc_h.push(self.x_h[-L0+1:self.x_h.size-L0+1]-self.xdc_mavg_h[0::]) # delay_cum[0]
        self.xschmidl_nodc.push(compute_schmidl_cox_with_hist(self.xnodc_h,l0)/l0) # delay_cum[1]
        if self.nread<self.delay_cum[1]: # if first run, null the history to avoid transients
            self.xschmidl_nodc[0:min((self.delay_cum[1]-self.nread),self.xschmidl_nodc.size)] = 0
        self.xschmidl_filt_nodc = interleaved_crosscorrelate_with_hist(self.xschmidl_nodc,self.lvl2_seq_diff,l0)/len(self.lvl2_seq_diff) # delay d[2]

        self.xcorr_nodc.push(np.abs(correlate_with_hist(self.xnodc_h,self.params.pseq_list_norm[0])/l0)**2) #delay delay1_cum[0]
        self.xcorr_filt_nodc = interleaved_sum_with_hist(self.xcorr_nodc,self.lvl2_len,l0)/self.lvl2_len # delay=delay1_cum[0]
        self.xcrossautocorr_nodc.push(np.abs(self.xschmidl_filt_nodc)*self.xcorr_filt_nodc)

        # NOTE: I need to create a view that a starts further in the past, bc if __max_margin__ is very small, peak1 may not be inside the window. I have to create the view here, bc self.xcrossautocorr may change its address when it grows in size
        # local_peaks2 = self.local_max_finder_h.work(self.xcrossautocorr_nodc)#self.xschmidl_filt_mag_nodc)
        xfinaltest = offset_array_view(self.xcrossautocorr_nodc.array_h,self.xcrossautocorr_nodc.hist_len-self.Ldiff,len(x))
        assert np.array_equal(xfinaltest[0::],self.xcrossautocorr_nodc[-self.Ldiff::])
        local_peaks = self.local_max_finder_h.work(xfinaltest,len(x))#self.xfinal_view,len(x))
        local_peaks = [l-self.Ldiff for l in local_peaks]
        # print 'peaks:',[p+self.nread-self.delay_cum[2] for p in local_peaks]

        for i in local_peaks:
            t = i-self.delay_cum[2]
            dc0 = self.xdc_mavg_h[t+L0] #np.mean(self.x_h[t:t+L0])
            peak0_mag2_nodc = np.mean(np.abs(self.x_h[t:t+L0]-dc0)**2)
#             # peak0_mag2 = np.mean(self.xmag2_h[t:t+self.pseq0_tot_len])
            xautocorr_nodc = np.sqrt(self.xcrossautocorr_nodc[i])#self.xschmidl_filt_mag_nodc[i]#np.sqrt(self.xcrossautocorr_nodc[i])#self.xschmidl_filt_mag_nodc[i]
#             # print 'time:',t+self.nread, peak0_mag2_nodc, xautocorr_nodc
            if xautocorr_nodc>self.thres1*peak0_mag2_nodc:
                # print 'peak:',t+self.nread,':',i+self.nread,xautocorr_nodc,'>',self.thres1*peak0_mag2_nodc
                tpeak,xcorr,cfo,l1mag2 = self.find_crosscorr_peak(t)
                dc_offset = np.mean(self.x_h[tpeak-self.awgn_len:tpeak])
                xmag2_mavg_nodc = np.mean(np.abs(self.x_h[tpeak:tpeak+L]-dc_offset)**2) # for the whole preamble
                # xmag2_mavg = np.mean(self.xmag2_h[tpeak:tpeak+L]) # for the whole preamble
                if l1mag2>0 and xcorr <= self.thres2*l1mag2:#xmag2_mavg_nodc:
                    continue
                # recompute values for the new peak
                # if tpeak!=t:
                #     xautocorr_nodc = self.xschmidl_filt_mag_nodc[tpeak+self.delay_cum[2]]
                awgn_estim_nodc = np.mean(np.abs(self.x_h[tpeak-self.awgn_len:tpeak]-dc_offset)**2)
                xautocorr_nodc = np.abs(self.xschmidl_filt_nodc[i])
                # awgn_estim = np.mean(self.xmag2_h[tpeak-self.awgn_len:tpeak])
                p = tracked_peak(tpeak+self.nread,xcorr,xautocorr_nodc,cfo,xmag2_mavg_nodc,awgn_estim_nodc,dc_offset)
                self.peaks.append(p)
                print p
        self.nread += x.size

def apply_cfo(x,cfo):
    return x * np.exp(1j*2*np.pi*cfo*np.arange(x.size),dtype=np.complex64)

def compensate_cfo(x,cfo):
    if type(cfo) is not list and type(cfo) is not np.ndarray:
        return x * np.exp(-1j*2*np.pi*cfo*np.arange(x.size),dtype=np.complex64)
    assert x.size==cfo.size
    return x * np.exp(-1j*2*np.pi*cfo,dtype=np.complex64)

