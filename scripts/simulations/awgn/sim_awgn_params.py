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

num_sections = 1
section_size = 50000
toffset_range = range(10,1000,100)
frequency_offset = [0]#np.linspace(-0.45,0.45,10)
skip_samps = 0
wf_gen_samps = section_size*num_sections + toffset_range[-1] + skip_samps + 50
settle_time = 1.0

# format_extension = 'pkl'
stage_names = ['waveform','Tx','RF'] # order matters
tags = ['sig_source']#,'wlan']

stage_params = {
    'sig_source':
    {
        'waveform':
        [
            ('waveform',['square','saw']),
            ('frequency',[1e4,1e5]),
            ('sample_rate',20e6),
            ('number_samples',wf_gen_samps),
            ('skip_samples',skip_samps)
        ],
        'Tx':
        [
            ('frequency_offset',frequency_offset),
            ('time_offset',toffset_range),
            ('section_size',section_size),
            ('num_sections',num_sections),
            ('soft_gain',10**np.arange(-2,1.0)),
            ('noise_voltage',[0])
        ],
        'RF':
        [
            ('tx_gain',range(0,30,5)),
            ('PLdB',-70),
            ('settle_time',1.0),
            ('awgndBm',-120),
            ('rx_gain',range(0,30,5))
        ],
        'Rx':
        [
            ('num_subsections_per_section',5)
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
