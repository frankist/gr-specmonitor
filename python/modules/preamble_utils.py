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
from basic_algorithms import *
import matplotlib.pyplot as plt

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
    pseq_list_coef = zadoffchu.barker_codes[barker_len]+[1]
    pseq_len_seq = [0]*barker_len+[1]
    return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

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

def get_schmidl_sequence(crosscorr_seq):
    schmidl_seq = [1]*(len(crosscorr_seq)-1)
    for i,p in enumerate(schmidl_seq):
        schmidl_seq[i] = np.exp(1j*(np.angle(crosscorr_seq[i+1])-np.angle(crosscorr_seq[i])))
    return schmidl_seq

class array_with_hist(object):# need to base it on object for negative slices
    def __init__(self,array,hist_len):
        self.hist_len = hist_len
        self.size = len(array)
        if type(array) is np.ndarray:
            self.array_h = np.append(np.zeros(hist_len,dtype=array.dtype),array)
        else:
            self.array_h = np.append(np.zeros(hist_len),array)

    def __str__(self):
        return '[{}]'.format(', '.join(str(i) for i in self.array_h))

    def capacity(self):
        return len(self.array_h)

    def resize(self,siz):
        if siz+self.hist_len > self.capacity():
            diff = siz+self.hist_len-self.capacity()
            self.array_h = np.append(self.array_h,np.zeros(diff,dtype=self.array_h.dtype))
            self.size = siz

    # def __len__(self):
    #     return self.size+self.hist_len

    def __getitem__(self,idx):
        # print 'wololo:',idx, self.size,self.size+self.hist_len
        if type(idx) is slice:
            start = idx.start+self.hist_len if idx.start is not None else None
            stop = idx.stop+self.hist_len if idx.stop is not None else None
            assert stop<=self.size+self.hist_len and start>=0
            return self.array_h[start:stop:idx.step]
            # assert idx.stop <= self.size
            # start = idx.start+self.hist_len if idx.start <= self.size else idx.start-self.size
            # stop = idx.stop+self.hist_len if idx.stop <= self.size else idx.stop-self.size
            # print 'wololo2:',start,stop
            # return self.array_h[start:stop]
        assert idx<=self.size+self.hist_len
        return self.array_h[idx+self.hist_len]

    def __setitem__(self,idx,value):
        if type(idx) is slice:
            self.array_h[idx.start+self.hist_len:idx.stop+self.hist_len:idx.step] = value
        else:
            self.array_h[idx+self.hist_len] = value

    def advance(self):
        self.array_h[0:self.hist_len] = self.array_h[self.size:self.size+self.hist_len]

    def push(self,x):
        assert x.dtype==self.array_h.dtype
        self.advance()
        self.resize(x.size)
        self.array_h[self.hist_len:self.hist_len+len(x)] = x

class tracked_peak:
    def __init__(self, tidx, xcorr_peak, xautocorr, cfo, xmag2, awgn_estim):
        self.tidx = tidx
        self.xcorr = xcorr_peak
        self.xautocorr = xautocorr
        self.cfo = cfo
        self.preamble_mag2 = xmag2
        self.awgn_mag2 = awgn_estim

    def __str__(self):
        return '[{}, {}, {}, {}, {}, {}]'.format(self.tidx,self.xcorr,self.xautocorr,self.cfo,self.preamble_mag2,self.awgn_mag2)

class PreambleDetectorType1:
    def __init__(self, fparams):#params, awgn_len):
        self.frame_params = fparams
        self.params = self.frame_params.preamble_params
        self.barker_len = len(self.params.pseq_list_seq)-1
        self.barker_vec = self.params.pseq_list_coef[0:-1]
        self.barker_diff = get_schmidl_sequence(self.barker_vec)
        self.pseq0 = self.params.pseq_list_norm[0]
        self.pseq0_tot_len = self.pseq0.size*self.barker_len
        self.awgn_len = self.frame_params.awgn_len
        self.hist_len = self.awgn_len + self.params.preamble_len
        self.hist_vec = []#np.zeros(self.hist_len)
        self.margin = 4
        self.thres1 = 0.4

        self.nread = 0
        self.peaks = []
        # self.max_peak = tracked_peak(-1,-1,-1,-1,-1,-1)

        # i keep these vars in mem for debug
        # self.x_h = []
        # self.xmag2_h = []
        self.xcorr_filt = np.array([],np.complex64)
        self.__max_margin__ = self.pseq0_tot_len
        # self.xmag2_mavg = []
        self.xschmidlmag2_h = []
        self.x_h = array_with_hist(np.array([],dtype=np.complex64),self.hist_len)
        self.xmag2_h = array_with_hist(np.array([],dtype=np.float32),self.hist_len)
        self.xschmidl = array_with_hist(np.array([],dtype=np.complex64),self.hist_len)
        self.xschmidl_filt = array_with_hist(np.array([],dtype=np.complex64),self.hist_len)
        self.xschmidl_filt_mag2 = array_with_hist(np.array([],dtype=np.float32),self.hist_len)
        self.xschmidl_filt_cfo = array_with_hist(np.array([],dtype=np.float32),self.hist_len)
        # self.mavg1_nodelay = no_delay_moving_average_ccc(self.pseq0_tot_len)

    def work(self,x):
        self.x_h.push(x) # [hist | x]
        self.xmag2_h.push(np.abs(x)**2)
        self.xschmidl.push(compute_schmidl_cox_with_hist(self.x_h,self.pseq0.size)/self.pseq0.size)
        xschmidl_delay = self.pseq0.size*2-1
        self.xschmidl_filt.push(interleaved_crosscorrelate_with_hist(self.xschmidl,self.barker_diff,self.pseq0.size))
        self.xschmidl_filt_mag2.push(np.abs(self.xschmidl_filt[0:self.xschmidl_filt.size]/len(self.barker_diff))**2)
        self.xschmidl_filt_cfo.push(-np.angle(self.xschmidl_filt[0:self.xschmidl_filt.size])/(2*np.pi*self.pseq0.size))
        xschmidl_filt_delay = xschmidl_delay+len(self.barker_diff)*self.pseq0.size

        assert self.xschmidl_filt.size == x.size
        assert self.xschmidl_filt_mag2.size == x.size
        start = -self.__max_margin__
        argmax_list = compute_local_maxima(self.xschmidl_filt_mag2[start:x.size],self.__max_margin__)
        argmax_list = [i+start for i in argmax_list]
        plt.plot(self.xschmidl_filt_mag2[start::])
        plt.show()

        plt.plot(np.abs(self.x_h[0:x.size])**2)
        plt.plot(np.abs(self.xmag2_h[0:x.size]),':')
        plt.plot([np.mean(self.xmag2_h[i:i+self.pseq0_tot_len]) for i in range(self.xmag2_h.size-self.pseq0_tot_len)])#moving avg
        plt.plot(np.abs(self.xschmidl[xschmidl_delay::]))
        plt.plot(self.xschmidl_filt_mag2[xschmidl_filt_delay::])
        plt.plot(self.xschmidl_filt_cfo[xschmidl_filt_delay::],'o')
        if len(argmax_list)>0:
            ymax_list = [self.xschmidl_filt_mag2[i] for i in argmax_list]
            plt.plot(np.array(argmax_list)-xschmidl_filt_delay,ymax_list/np.max(ymax_list),'x')
        plt.show()

        for i in argmax_list:
            t = i-xschmidl_filt_delay
            xmag2_mavg = np.mean(self.xmag2_h[t:t+self.pseq0_tot_len])
            # print 'time:',t+self.nread
            if self.xschmidl_filt_mag2[i]>self.thres1*xmag2_mavg:
                # print 'peak:',self.xschmidl_filt_mag2[i], self.thres1*xmag2_mavg
                # compensate cfo
                cfo = self.xschmidl_filt_cfo[i]
                y=compensate_cfo(self.x_h[t-self.margin:t+self.params.length()+self.margin],cfo)
                ycorr = np.correlate(y,self.params.preamble)
                plt.show()
                maxi = np.argmax(np.abs(ycorr))
                xcorr = np.abs(ycorr[maxi])/self.params.length()
                # print xcorr,maxi
                # plt.plot(y[maxi::])
                # plt.plot(self.params.preamble,':')
                # plt.show()
                xautocorr = self.xschmidl_filt_mag2[i]
                awgn_estim = np.mean(self.xmag2_h[t-self.awgn_len:t])
                p = tracked_peak(t+self.nread,xcorr,xautocorr,cfo,xmag2_mavg,awgn_estim)
                self.peaks.append(p)
                print p
        self.nread += x.size

def compute_local_maxima(x,margin):
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
    return l

def compute_schmidl_cox_peak(x,nBins_half):
    dim = x.size-2*nBins_half+1
    delayed_xmult = np.zeros(dim,dtype='complex64')
    for k in range(dim):
        delayed_xmult[k] = np.sum(x[k:k+nBins_half]*np.conj(x[k+nBins_half:k+2*nBins_half]))
    return delayed_xmult

def compute_schmidl_cox_with_hist(x_h,nBins_half):
    return compute_schmidl_cox_peak(x_h[-nBins_half*2+1:x_h.size],nBins_half)

def interleaved_crosscorrelate(x1,x2,interleav_len):
    winsize = interleav_len*len(x2)
    y = np.zeros(x1.size-winsize, dtype=np.complex64)
    for i in range(y.size):
        xx = x1[i:i+winsize:interleav_len]
        y[i] = np.sum(xx*x2)
    return y

def interleaved_crosscorrelate_with_hist(x_h,x2,interleav_len):
    winsize = interleav_len*len(x2)
    x = x_h[-winsize:x_h.size]
    return interleaved_crosscorrelate(x,x2,interleav_len)

class no_delay_moving_average_ccc:
    def __init__(self,size):
        self.mavg = moving_average_ccc(size)
        self.out = array_with_hist([],size-1)

    def work(self,x):
        self.out.resize(x.size)
        self.out[-self.out.hist_len:-self.out.hist_len+x.size] = self.mavg.work(x)

def interleaved_sum(x1,num_sums,interleav_len):
    winsize = interleav_len*num_sums
    y = np.zeros(x1.size-winsize,dtype=np.complex64)
    for i in range(y.size):
        xx = x1[i:i+winsize:interleav_len]
        y[i] = np.sum(np.abs(xx))
    return y

def apply_cfo(x,cfo):
    return x * np.exp(1j*2*np.pi*cfo*np.arange(x.size),dtype=np.complex64)

def compensate_cfo(x,cfo):
    return x * np.exp(-1j*2*np.pi*cfo*np.arange(x.size))

def estimate_cfo(x,maxi,halfBins):
    xcopy_peak = np.sum(x[maxi:maxi+halfBins]*np.conj(x[maxi+halfBins:maxi+2*halfBins]))
    return -np.angle(xcopy_peak)/(2*halfBins*np.pi)
