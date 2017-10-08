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

class tracked_peak:
    def __init__(self, tidx, xcorr_peak, xautocorr, cfo, xmag2, awgn_estim):
        self.tidx = tidx
        self.xcorr = xcorr_peak
        self.xautocorr = xautocorr
        self.cfo = cfo
        self.preamble_mag2 = xmag2
        self.awgn_mag2 = awgn_estim

class PreambleDetectorType1:
    def __init__(self, fparams):#params, awgn_len):
        self.frame_params = fparams
        self.params = self.frame_params.preamble_params
        self.barker_len = len(self.params.pseq_list_seq)-1
        self.barker_vec = self.params.pseq_list_seq[0:-1]
        self.barker_diff = get_schmidl_sequence(self.barker_vec)
        self.pseq0 = self.frame_params.preamble.pseq_list_norm[0]
        self.pseq0_tot_len = self.pseq0.size*self.barker_len
        self.awgn_len = awgn_len
        self.hist_len = self.awgn_len + self.params.preamble_len
        self.hist_vec = []#np.zeros(self.hist_len)
        self.margin = 4
        self.awgn_len = 100

        self.nread = 0
        self.max_peak = tracked_peak(-1,-1,-1,-1,-1)

        # i keep these vars in mem for debug
        self.x_with_hist = []
        self.xcorr = []
        self.xcorr_filt = []

    def find_xcorr_peak(self,x,max_i,margin,cfo):
        xcorr_max = -1
        xcorr_max_i = -1
        x_nocfo = compensate_cfo(x[max_i-margin:max_i+margin+self.params.preamble_len],p.cfo)
        for i in range(2*margin):
            xcorr = np.correlate(x_nocfo[i:i+self.params.preamble_len],self.params.preamble)
            if np.abs(xcorr) > xcorr_max:
                xcorr_max = np.abs(xcorr)
                xcorr_max_i = i
        return (xcorr_max,xcorr_max_i-margin)

    def work(self,x):
        self.x_with_hist = np.append(self.hist_vec,x)
        self.xcorr = np.correlate(x_with_hist,self.pseq0)

        max_n = xcorr.size-self.hist_len
        self.xcorr_filt = np.zeros(max_n)
        for i in range(max_n):
            v = xcorr[i:i+self.pseq0_tot_len:self.pseq0.size]
            assert v.size == self.barker_len
            self.xcorr_filt[i] = np.sum(v*self.barker_len)
        max_i = np.argmax(np.abs(self.xcorr_filt))

        pseq0_tot = x_with_hist[max_i:max_i+self.pseq0_tot_len]
        xautocorr = compute_schmidl_cox_peak(pseq0_tot,self.pseq0.size)
        xschmidl = np.sum(xautocorr*self.barker_diff)
        xmag2 = np.mean(np.abs(x_with_hist[max_i:max_i+self.preamble_len])**2)
        awgn_estim = np.mean(np.abs(x_with_hist[max_i-self.awgn_len:max_i])**2)

        p = tracked_peak(self.nread+max_i, -1, np.abs(xschmidl)**2, -np.angle(2*np.pi*self.pseq0.size), xmag2, awgn_estim)
        p.xcorr,toff = self.find_xcorr_peak(x_with_hist,max_i,self.margin,p.cfo)
        p.tidx += toff
        if p.xcorr > self.max_peak.xcorr:
            self.max_peak = p

        self.hist_vec = x_with_hist[-self.hist_len::]
        assert self.hist_vec.size == self.hist_len
        self.nread += x.size

def compute_schmidl_cox_peak(x,nBins_half):
    delayed_xmult = np.zeros(x.size-nBins_half,dtype='complex64')
    for k in range(x.size-2*nBins_half):
        delayed_xmult[k] = np.sum(x[k:k+nBins_half]*np.conj(x[k+nBins_half:k+2*nBins_half]))
    return delayed_xmult

def apply_cfo(x,cfo):
    return x * np.exp(1j*2*np.pi*cfo*np.arange(x.size))

def compensate_cfo(x,cfo):
    return x * np.exp(-1j*2*np.pi*cfo*np.arange(x.size))

def estimate_cfo(x,maxi,halfBins):
    xcopy_peak = np.sum(x[maxi:maxi+halfBins]*np.conj(x[maxi+halfBins:maxi+2*halfBins]))
    return -np.angle(xcopy_peak)/(2*halfBins*np.pi)
