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
sys.path.append('../../../python/labeling_modules')
sys.path.append('../../../python/utils')
import metadata_handler as mh
import session_params as sparams
import numpy as np

# format_extension = 'pkl'
stage_names = ['waveform','Tx'] # order matters
tags = ['sig_source']#,'wlan']

stage_params = {
    'sig_source':
    {
        'waveform':
        [
            ('waveform',['square','saw']),
            ('frequency',[1e3,1e4,1e5]),
            ('sample_rate',20e6),
            ('number_samples',1e6),
            ('skip_samples',0)
        ],
        'Tx':
        [
            ('frequency_offset',np.linspace(-0.3,0.3,10)),
            ('time_offset',range(10))
        ]
    }
    # 'wlan':
    # {
    #     'waveform':
    #     [
    #         ('waveform',['wlan']),
    #     ],
    #     'Tx':
    #     [
    #         ('frequency_offset',np.linspace(-0.4,0.4,100))
    #     ]
    # }
}

# SignalSource_params = mh.ParamProductJoin([[
#     ('waveform',['square','saw']),
#     ('sample_rate',20e6),
#     ('frequency',[1e3,1e4,1e5]),
#     ('number_samples',1e6),
#     ('skip_samples',0)
# ]])

# TX_params = mh.ParamProductJoin([[
#     ('frequency_offset',np.linspace(-0.3,0.3,100))
# ]])

# stage_params = [SignalSource_params,TX_params]

if __name__ == '__main__':
    # print mh.LabeledParamValues('waveform',['square','triangle']).to_tuple()
    for v in staged_params.get_iterable('sig_source','Tx'):
        print v
