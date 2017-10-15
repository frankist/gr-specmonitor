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

import zadoffchu
import numpy as np
import sys
import matplotlib.pyplot as plt
from basic_algorithms import *

# min_idx = 0

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
def generate_preamble_type1(pseq_len_list, barker_len):
    assert len(pseq_len_list)==2
    pseq_list = [zadoffchu.generate_sequence(p,1,0) for p in pseq_len_list]
    # pseq_dc_list = [np.mean(pseq_list[i]) for i in range(len(pseq_len_list))]
    # pseq_list = [pseq_list[i]-pseq_dc_list[i] for i in range(len(pseq_len_list))]
    pseq_list_coef = zadoffchu.barker_codes[barker_len]+[1]
    pseq_len_seq = [0]*barker_len+[1]
    return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

def generate_preamble_type2(pseq_len_list, barker_len, num_repeats):
    assert len(pseq_len_list)==2
    pseq_list = [zadoffchu.generate_sequence(p,1,0) for p in pseq_len_list]
    barkercode = zadoffchu.barker_codes[barker_len]
    barkercode_many = np.array([])
    for i in range(num_repeats):
        barkercode_many = np.append(barkercode_many,barkercode)
    pseq_list_coef = set_schmidl_sequence(barkercode_many)
    pseq_list_coef = np.append(pseq_list_coef,1)
    pseq_len_seq = [0]*(barker_len*num_repeats+1)+[1]
    return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

def get_schmidl_sequence(crosscorr_seq):
    schmidl_seq = [1]*(len(crosscorr_seq)-1)
    for i,p in enumerate(schmidl_seq):
        schmidl_seq[i] = np.exp(1j*(np.angle(crosscorr_seq[i+1])-np.angle(crosscorr_seq[i])))
    return schmidl_seq

def set_schmidl_sequence(autocorr_seq):
    crosscorr_seq = [1]*(len(autocorr_seq)+1)
    for i in range(1,len(autocorr_seq)):
        crosscorr_seq[i] = np.exp(1j*(np.angle(crosscorr_seq[i-1])+np.angle(autocorr_seq[i-1])))
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
        nread = self.frame_params.section_duration()*num_sections+2*self.frame_params.guard_len
        nwritten = self.frame_params.frame_period*num_sections
        assert x.size>=nread

        T = self.frame_params.frame_period
        T0 = self.frame_params.section_duration()
        framed_signal = np.zeros(nwritten,np.complex64)
        for i in range(num_sections):
            framed_signal[i*T:(i+1)*T] = self.generate_framed_section(x[i*T0:(i+1)*T0+2*self.frame_params.guard_len])
        section_ranges = self.get_framed_section_ranges(num_sections)

        return (framed_signal,section_ranges)

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

class PreambleDetectorType1:
    def __init__(self, fparams, thres1=0.3, thres2=0.3):#params, awgn_len):
        self.frame_params = fparams
        self.thres1 = thres1
        self.thres2 = thres2

        # derived
        self.params = self.frame_params.preamble_params
        self.barker_len = len(self.params.pseq_list_seq)-1
        self.barker_vec = self.params.pseq_list_coef[0:-1]
        self.barker_diff = get_schmidl_sequence(self.barker_vec)
        self.pseq0 = self.params.pseq_list_norm[0]
        self.pseq0_tot_len = self.pseq0.size*self.barker_len
        self.awgn_len = self.frame_params.awgn_len
        self.hist_len = self.awgn_len + self.params.preamble_len
        self.margin = 16

        self.nread = 0
        self.peaks = []

        # i keep these vars in mem for debug
        # self.x_h = []
        # self.xmag2_h = []
        self.xcorr_filt = np.array([],np.complex64)
        self.__max_margin__ = self.pseq0_tot_len
        self.delay = [self.pseq0_tot_len, self.pseq0.size*2-1, len(self.barker_diff)*self.pseq0.size]
        self.delay_cum = np.cumsum(self.delay)
        # self.hist_len2 = self.hist_len+self.__max_margin__+self.delay_cum[0]
        self.hist_len2 = np.sum(self.delay_cum[1:3])+self.params.length()+self.awgn_len+2*self.margin
        # self.xmag2_mavg = []
        self.xschmidlmag2_h = []
        self.x_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)# check if this size is fine
        self.xdc_mavg_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)# check if this size is fine
        self.xnodc_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)
        self.xschmidl_nodc = array_with_hist(np.array([],dtype=np.complex64),self.hist_len)# check if this size is fine
        self.xschmidl_filt_nodc = array_with_hist(np.array([],dtype=np.complex64),self.__max_margin__)
        self.xschmidl_filt_mag2_nodc = array_with_hist(np.array([],dtype=np.float32),self.__max_margin__)

        self.local_max_finder_h = sliding_window_max_hist(self.__max_margin__)

    def find_crosscorr_peak(self,tpeak): # this is for high precision time sync
        # compensate CFO
        cfo = compute_schmidl_cox_cfo(self.xschmidl_filt_nodc[tpeak+self.delay_cum[2]],self.pseq0.size)
        if np.abs(tpeak-75)<4:
            print '(t,cfo):',tpeak,cfo
        twin = (tpeak-self.margin,tpeak+self.params.length()+self.margin)
        # dc_mavg2 = np.array([np.mean(self.x_h[i:i+self.params.length()]) for i in range(twin[0],twin[1])])
        # print twin[0]-self.awgn_len, self.x_h.hist_len
        # global min_idx
        # min_idx = min(min_idx,twin[0]-self.awgn_len)
        dc_mavg2 = np.array([np.mean(self.x_h[i-self.awgn_len:i]) for i in range(twin[0],twin[1])])
        xnodc = self.x_h[twin[0]:twin[1]]-dc_mavg2
        y = compensate_cfo(xnodc,cfo)
        # y = compensate_cfo(self.x_h[tpeak-self.margin:tpeak+self.params.length()+self.margin],cfo)
        ycorr = np.correlate(y,self.params.preamble)
        maxi = np.argmax(np.abs(ycorr))
        xcorr = np.abs(ycorr[maxi]/self.params.length())**2
        tnew = tpeak + maxi-self.margin
        if tnew!=tpeak:
            cfo = compute_schmidl_cox_cfo(self.xschmidl_filt_nodc[tnew+self.delay_cum[2]],self.pseq0.size)
        # plt.plot(np.abs(ycorr))
        # plt.show()
        # visualization: compare preamble with signal to see if they match in shape
        # print xcorr,maxi,tpeak,tnew,cfo
        # plt.plot(self.params.preamble)
        # ytmp = y[maxi:maxi+self.params.length()]
        # ytmp = ytmp*np.exp(-1j*np.angle(ytmp[0]/self.params.preamble[0])) # align phase for comparison
        # plt.plot(ytmp,'x')
        # plt.show()
        return (tnew,xcorr,cfo)

    def work(self,x):
        l0 = self.pseq0.size
        L0 = self.delay_cum[0]
        L = self.params.length()
        # print 'window:',self.nread,self.nread+x.size
        self.x_h.push(x) # [hist | x]
        self.xdc_mavg_h.push(moving_average_with_hist(self.x_h,L0)) # delay=d[0]
        self.xnodc_h.push(self.x_h[-L0:self.x_h.size-L0]-self.xdc_mavg_h[0::]) # delay=d[0]
        self.xschmidl_nodc.push(compute_schmidl_cox_with_hist(self.xnodc_h,l0)/l0) # delay d[1]
        self.xschmidl_filt_nodc.push(interleaved_crosscorrelate_with_hist(self.xschmidl_nodc,self.barker_diff,l0)/len(self.barker_diff)) # delay d[2]
        self.xschmidl_filt_mag2_nodc.push(np.abs(self.xschmidl_filt_nodc[0::]))

        # if self.xschmidl_filt.size>=self.xschmidl_filt_delay:
        #     assert np.max(np.abs(np.abs(xtmp[0::])**2-self.xschmidl_filt_mag2[self.xschmidl_filt_delay::]))<0.00001

        local_peaks = self.local_max_finder_h.work(self.xschmidl_filt_mag2_nodc)
        print 'peaks:',[p-self.delay_cum[2] for p in local_peaks]

        for i in local_peaks:
            t = i-self.delay_cum[2]
            dc0 = self.xdc_mavg_h[t+L0] #np.mean(self.x_h[t:t+L0])
            peak0_mag2_nodc = np.mean(np.abs(self.x_h[t:t+L0]-dc0)**2)
            # peak0_mag2 = np.mean(self.xmag2_h[t:t+self.pseq0_tot_len])
            xautocorr_nodc = self.xschmidl_filt_mag2_nodc[i]
            # print 'time:',t+self.nread, peak0_mag2_nodc, xautocorr_nodc
            if xautocorr_nodc>self.thres1*peak0_mag2_nodc:
                tpeak,xcorr,cfo = self.find_crosscorr_peak(t)
                dc_offset = np.mean(self.x_h[tpeak-self.awgn_len:tpeak])
                xmag2_mavg_nodc = np.mean(np.abs(self.x_h[tpeak:tpeak+L]-dc_offset)**2) # for the whole preamble
                # xmag2_mavg = np.mean(self.xmag2_h[tpeak:tpeak+L]) # for the whole preamble
                if xcorr <= self.thres2*xmag2_mavg_nodc:
                    continue
                # recompute values for the new peak
                if tpeak!=t:
                    xautocorr_nodc = self.xschmidl_filt_mag2_nodc[tpeak+self.delay_cum[2]]
                awgn_estim_nodc = np.mean(np.abs(self.x_h[tpeak-self.awgn_len:tpeak]-dc_offset)**2)
                # awgn_estim = np.mean(self.xmag2_h[tpeak-self.awgn_len:tpeak])
                p = tracked_peak(tpeak+self.nread,xcorr,xautocorr_nodc,cfo,xmag2_mavg_nodc,awgn_estim_nodc,dc_offset)
                self.peaks.append(p)
                # print p
        self.nread += x.size

class PreambleDetectorType2:
    def __init__(self, fparams, barker_seq0, thres1=0.3, thres2=0.3):#params, awgn_len):
        self.frame_params = fparams
        self.barker_seq0 = barker_seq0
        self.thres1 = thres1
        self.thres2 = thres2

#         # derived
        self.params = self.frame_params.preamble_params
        self.barker_len = len(self.params.pseq_list_seq)-1
#         self.pseq0_lvl2_len = len(self.params.pseq_list_seq)-1
        self.barker_vec = self.params.pseq_list_coef[0:-1]
        self.barker_diff = get_schmidl_sequence(self.barker_vec)
        self.pseq0 = self.params.pseq_list_norm[0]
        self.pseq0_lvl2_len = self.pseq0.size*self.barker_len
        self.awgn_len = self.frame_params.awgn_len
        self.hist_len = self.awgn_len + self.params.preamble_len
        self.margin = 16

        self.nread = 0
        self.peaks = []

        # i keep these vars in mem for debug
        self.x_h = []
#         # # self.xmag2_h = []
#         # self.xcorr_filt = np.array([],np.complex64)
        self.__max_margin__ = self.barker_seq0*self.pseq0.size
        self.delay = [self.pseq0_lvl2_len, self.pseq0.size*2-1, len(self.barker_diff)*self.pseq0.size]
        self.delay_cum = np.cumsum(self.delay)
#         # # self.hist_len2 = self.hist_len+self.__max_margin__+self.delay_cum[0]
        self.hist_len2 = np.sum(self.delay_cum[1:3])+self.params.length()+self.awgn_len+2*self.margin
#         # # self.xmag2_mavg = []
#         # self.xschmidlmag2_h = []
        self.x_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)# check if this size is fine
        self.xdc_mavg_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)# check if this size is fine
        self.xnodc_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len2)
        self.xschmidl_nodc = array_with_hist(np.array([],dtype=np.complex64),self.hist_len)# check if this size is fine
        self.xschmidl_filt_nodc = array_with_hist(np.array([],dtype=np.complex64),self.__max_margin__)
        self.xschmidl_filt_mag_nodc = array_with_hist(np.array([],dtype=np.float32),self.__max_margin__)

        self.local_max_finder_h = sliding_window_max_hist(self.__max_margin__)

#     def find_crosscorr_peak(self,tpeak): # this is for high precision time sync
#         # compensate CFO
#         cfo = compute_schmidl_cox_cfo(self.xschmidl_filt_nodc[tpeak+self.delay_cum[2]],self.pseq0.size)
#         if np.abs(tpeak-75)<4:
#             print '(t,cfo):',tpeak,cfo
#         twin = (tpeak-self.margin,tpeak+self.params.length()+self.margin)
#         # dc_mavg2 = np.array([np.mean(self.x_h[i:i+self.params.length()]) for i in range(twin[0],twin[1])])
#         # print twin[0]-self.awgn_len, self.x_h.hist_len
#         # global min_idx
#         # min_idx = min(min_idx,twin[0]-self.awgn_len)
#         dc_mavg2 = np.array([np.mean(self.x_h[i-self.awgn_len:i]) for i in range(twin[0],twin[1])])
#         xnodc = self.x_h[twin[0]:twin[1]]-dc_mavg2
#         y = compensate_cfo(xnodc,cfo)
#         # y = compensate_cfo(self.x_h[tpeak-self.margin:tpeak+self.params.length()+self.margin],cfo)
#         ycorr = np.correlate(y,self.params.preamble)
#         maxi = np.argmax(np.abs(ycorr))
#         xcorr = np.abs(ycorr[maxi]/self.params.length())**2
#         tnew = tpeak + maxi-self.margin
#         if tnew!=tpeak:
#             cfo = compute_schmidl_cox_cfo(self.xschmidl_filt_nodc[tnew+self.delay_cum[2]],self.pseq0.size)
#         # plt.plot(np.abs(ycorr))
#         # plt.show()
#         # visualization: compare preamble with signal to see if they match in shape
#         # print xcorr,maxi,tpeak,tnew,cfo
#         # plt.plot(self.params.preamble)
#         # ytmp = y[maxi:maxi+self.params.length()]
#         # ytmp = ytmp*np.exp(-1j*np.angle(ytmp[0]/self.params.preamble[0])) # align phase for comparison
#         # plt.plot(ytmp,'x')
#         # plt.show()
#         return (tnew,xcorr,cfo)

    def work(self,x):
        l0 = self.pseq0.size
        L0 = self.delay_cum[0]
        L = self.params.length()
        # print 'window:',self.nread,self.nread+x.size
        self.x_h.push(x) # [hist | x]
        self.xdc_mavg_h.push(moving_average_with_hist(self.x_h,L0)) # delay=d[0]
        self.xnodc_h.push(self.x_h[-L0:self.x_h.size-L0]-self.xdc_mavg_h[0::]) # delay=d[0]
        self.xschmidl_nodc.push(compute_schmidl_cox_with_hist(self.xnodc_h,l0)/l0) # delay d[1]
        self.xschmidl_filt_nodc.push(interleaved_crosscorrelate_with_hist(self.xschmidl_nodc,self.barker_diff,l0)/len(self.barker_diff)) # delay d[2]
        self.xschmidl_filt_mag_nodc.push(np.abs(self.xschmidl_filt_nodc[0::]))

        local_peaks = self.local_max_finder_h.work(self.xschmidl_filt_mag_nodc)
#         print 'peaks:',[p-self.delay_cum[2] for p in local_peaks]

#         for i in local_peaks:
#             t = i-self.delay_cum[2]
#             dc0 = self.xdc_mavg_h[t+L0] #np.mean(self.x_h[t:t+L0])
#             peak0_mag2_nodc = np.mean(np.abs(self.x_h[t:t+L0]-dc0)**2)
#             # peak0_mag2 = np.mean(self.xmag2_h[t:t+self.pseq0_tot_len])
#             xautocorr_nodc = self.xschmidl_filt_mag2_nodc[i]
#             # print 'time:',t+self.nread, peak0_mag2_nodc, xautocorr_nodc
#             if xautocorr_nodc>self.thres1*peak0_mag2_nodc:
#                 tpeak,xcorr,cfo = self.find_crosscorr_peak(t)
#                 dc_offset = np.mean(self.x_h[tpeak-self.awgn_len:tpeak])
#                 xmag2_mavg_nodc = np.mean(np.abs(self.x_h[tpeak:tpeak+L]-dc_offset)**2) # for the whole preamble
#                 # xmag2_mavg = np.mean(self.xmag2_h[tpeak:tpeak+L]) # for the whole preamble
#                 if xcorr <= self.thres2*xmag2_mavg_nodc:
#                     continue
#                 # recompute values for the new peak
#                 if tpeak!=t:
#                     xautocorr_nodc = self.xschmidl_filt_mag2_nodc[tpeak+self.delay_cum[2]]
#                 awgn_estim_nodc = np.mean(np.abs(self.x_h[tpeak-self.awgn_len:tpeak]-dc_offset)**2)
#                 # awgn_estim = np.mean(self.xmag2_h[tpeak-self.awgn_len:tpeak])
#                 p = tracked_peak(tpeak+self.nread,xcorr,xautocorr_nodc,cfo,xmag2_mavg_nodc,awgn_estim_nodc,dc_offset)
#                 self.peaks.append(p)
#                 # print p
#         self.nread += x.size

def apply_cfo(x,cfo):
    return x * np.exp(1j*2*np.pi*cfo*np.arange(x.size),dtype=np.complex64)

def compensate_cfo(x,cfo):
    if type(cfo) is not list and type(cfo) is not np.ndarray:
        return x * np.exp(-1j*2*np.pi*cfo*np.arange(x.size),dtype=np.complex64)
    assert x.size==cfo.size
    return x * np.exp(-1j*2*np.pi*cfo,dtype=np.complex64)
