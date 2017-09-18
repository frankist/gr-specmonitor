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
        preamble = np.zeros(self.preamble_len,dtype='complex64')
        n=0
        for i,p in enumerate(pseq_list_seq):
            preamble[n:n+self.pseq_list[p].size] = self.pseq_list[p] * self.pseq_list_coef[i]
            n = n+self.pseq_list[p].size
        preamble /= np.sqrt(np.mean(np.abs(self.preamble)**2))
        return preamble

def generate_type1(pseq_len_list, barker_len,):
    pseq_list = []
    for i,v in enumerate(pseq_len_list):
        pseq_list.append(zadoffchu.generate_sequence(v,1,0))
    pseq_len_coef = zadoffchu.barker_codes[barker_len]
    pseq_len_coef.append(1)
    pseq_len_seq = [0]*barker_len
    pseq_len_seq.append(1)
    return preamble_params(pseq_list,pseq_len_seq,pseq_list_coef)

def find_type1(p_params):


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
