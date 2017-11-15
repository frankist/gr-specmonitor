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
# sys.path.append('../../../python/modules')
# sys.path.append('../../../python/labeling_modules')
# sys.path.append('../../../python/utils')
import numpy as np

num_sections = 1
section_size = 50000
toffset_range = range(10,1000,500)
frequency_offset = np.linspace(-0.1,0.1,2)
skip_samps = 0
wf_gen_samps = section_size*num_sections + toffset_range[-1] + skip_samps + 50
img_fft = 64 # the size of the FFT that is going to be used for the image generation

# stage_names = ['waveform','Tx','RF'] # order matters # NOTE: Consider deleting this
tags = ['sig','wifi','psk']#,'wlan'] # NOTE: Consider deleting this
ssh_hosts = ['USRPRx']
stage_dependency_tree = {
    'Tx':'waveform',
    'RF':'Tx',
    'TxImg':'Tx',
    'RFImg':'RF'
}

Tx_params = [
    ('frequency_offset',frequency_offset),
    ('time_offset',toffset_range),
    ('section_size',section_size),
    ('num_sections',num_sections),
    ('soft_gain',[0.1,1.0]),#10**np.arange(-2,1.0)),
    ('noise_voltage',[0])
]
Tx_params_wifi = list(Tx_params)
for e in Tx_params_wifi:
    if e[0]=='frequency_offset':
        e = ('frequency_offset',0)

RF_params = [
    ('tx_gain_norm', 10.0**np.arange(-20,0,5)),#range(0, 21, 10)),  #range(0,30,15)),
    ('settle_time', 0.25),
    ('rx_gaindB', range(0, 21, 10)),
    ('rf_frequency', 2.35e9)
]

stage_params = {
    'wifi':
    {
        'waveform':
        [
            ('waveform',['wifi']),
            ('number_samples',wf_gen_samps),
            ('sample_rate',20e6),
            ('encoding',[0]),#range(0,7)),
            ('pdu_length',[500,750,1000,1250]), # 50-1500
            ('pad_interval',5000) # spaces between packets. I may make it random
        ],
        'Tx': Tx_params_wifi,
        'RF': RF_params
    },
    'sig':
    {
        'waveform':
        [
            ('waveform',['square','saw']),
            ('sample_rate',20e6),
            ('frequency',[1e4,5e5]),
            ('number_samples',wf_gen_samps)
            # ('skip_samples',skip_samps)
        ],
        'Tx': Tx_params,
        'RF': RF_params
    },
    'psk':
    {
        'waveform':
        [
            ('waveform',['generic_mod']),
            ('sample_rate',20e6),
            ('number_samples',wf_gen_samps),
            ('constellation',['psk']),
            ('order',[2,4]),
            ('mod_code','GRAY'),
            ('differential',False),
            ('samples_per_symbol',10),
            ('excess_bw',0.25),
            ('pre_diff_code',False),
            ('burst_len',5000),
            ('zero_pad_len',5000)
        ],
        'Tx': Tx_params,
        'RF': RF_params
    }
}

if __name__ == '__main__':
    for v in staged_params.get_iterable('sig','Tx'):
        print v
