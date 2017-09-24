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

def generate_sequence(zc_length, u, q, n_start = 0, num_samples = -1):
    if num_samples < 0:
        num_samples = zc_length
    n_end = n_start + num_samples

    zc = [0]*num_samples#np.zeros(num_samples, dtype='complex')
    zc[0:num_samples] = [np.exp(np.complex(0,-1.0*np.pi*u*float(n*(n+1+2*q))/zc_length)) for n in range(n_start,n_end)]

    return np.array(zc)

