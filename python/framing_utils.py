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
import zadoffchu
import json

def generate_preamble(zc_len, n_repeats):
    pseq_list = []
    pseq_norm_list = []
    for p in zc_len:
        pseq = zadoffchu.generate_sequence(p,1,0)
        pseq_list.append(pseq)
        pseq_norm = pseq / np.sqrt(np.sum(np.abs(pseq)**2))
        pseq_norm_list.append(pseq_norm)
    n_samples = np.sum([zc_len[i]*n_repeats[i] for i in range(len(zc_len))])
    x = np.zeros(n_samples,dtype=np.complex128)
    t = 0
    for i in range(len(zc_len)):
        for r in range(n_repeats[i]):
            x[t:t+zc_len[i]] = pseq_list[i]
            t = t + zc_len[i]

    return (x,pseq_list,pseq_norm_list)

class frame_params:
    def __init__(self, pseq_vec, n_repeats, frame_period, awgn_len, guard_period):
        self.pseq_vec = pseq_vec
        self.n_repeats = n_repeats
        self.frame_period = frame_period
        self.awgn_len = awgn_len
        self.guard_period = guard_period

    def to_json(self):
        d = self.__dict__.copy()
        for i,vec in enumerate(d['pseq_vec']):
            l = [[float(np.real(vec[j])),float(np.imag(vec[j]))] for j in range(len(vec))]
            d['pseq_vec'][i] = l
        return d#json.dumps(d)

if __name__ == '__main__':
    # test the json serialization
    pseq_vec = []
    pseq_vec.append(np.array([1+1j,1+2j],dtype='complex64'))
    pseq_vec.append(np.array([1,2-1j],dtype='complex64'))
    f = frame_params(pseq_vec, [3,1], 1000, 100, 2)
    j = f.to_json()
    assert(len(j['n_repeats'])==2)
    assert(j['n_repeats'][0]==3)
    assert(j['n_repeats'][1]==1)
    assert(len(j['pseq_vec'])==2)
    assert(j['pseq_vec'][0][0]==[1.0,1.0])
    assert(j['pseq_vec'][0][1]==[1.0,2.0])
    assert(j['pseq_vec'][1][0]==[1.0,0.0])
    assert(j['pseq_vec'][1][1]==[2.0,-1.0])
    assert(j['awgn_len']==100)
    assert(j['guard_period']==2)

