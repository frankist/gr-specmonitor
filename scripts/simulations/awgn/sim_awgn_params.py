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

import sys
sys.path.append('../../../python/modules')
import metadata_handler as mh
import numpy as np

# format_extension = 'pkl'
stage_names = ['waveform','Tx']

SignalSource_params = mh.ParamProductJoin([[
    ('waveform',['square','saw']),
    ('sample_rate',20e6),
    ('frequency',[1e3,1e4,1e5,1e6]),
    ('number_samples',1e6),
    ('skip_samples',0)
]])

TX_params = mh.ParamProductJoin([[
    ('frequency_offset',np.linspace(-0.3,0.3,100))
]])

stage_params = [SignalSource_params,TX_params]

