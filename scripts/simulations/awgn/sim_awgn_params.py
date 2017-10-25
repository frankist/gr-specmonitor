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
import session_params as sparams
import numpy as np

num_sections = 1
section_size = 50000
toffset_range = range(10,1000,500)
frequency_offset = np.linspace(-0.4,0.4,3)
skip_samps = 0
wf_gen_samps = section_size*num_sections + toffset_range[-1] + skip_samps + 50
img_fft = 64 # the size of the FFT that is going to be used for the image generation

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
            ('soft_gain',1.0),#10**np.arange(-2,1.0)),
            ('noise_voltage',[0])
        ],
        'RF':
        [
            ('tx_gaindB',range(0,30,15)),
            ('PLdB',0),#150),
            ('settle_time',0.01),
            ('awgndBm',-120),
            ('rx_gaindB',range(0,30,15))
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

if __name__ == '__main__':
    for v in staged_params.get_iterable('sig_source','Tx'):
        print v
