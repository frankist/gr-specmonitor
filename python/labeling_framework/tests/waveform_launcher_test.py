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
import sys
import os
import matplotlib.pyplot as plt

# load labeling_framework package
sys.path.append('../../')#os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# load file to test
from labeling_framework.waveform_generators import waveform_launcher
from labeling_framework.sig_format import pkl_sig_format
import logging

square_wf_params = {
    'waveform': 'square',
    'sample_rate': 10.0e6,
    'frequency': 1.0e3,
    'number_samples': 100000,
}

wifi_wf_params = {
    'waveform': 'wifi',
    'number_samples': 100000,
    'encoding': 0,
    'pdu_length': 500,
    'pad_interval': 5000,
}

psk_wf_params = {
    'waveform':'generic_mod',
    'number_samples': 100000,
    'constellation':'psk',
    'order':2,
    'mod_code':'GRAY',
    'differential':False,
    'samples_per_symbol':10,
    'excess_bw':0.25,
    'pre_diff_code':False,
    'burst_len':5000,
    'zero_pad_len':5000,
}

if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    targetfile = '~/tmp/out.pkl'
    args = {
        # 'parameters': square_wf_params,
        # 'parameters': wifi_wf_params,
        'parameters': psk_wf_params,
        'targetfilename': targetfile,
        'stage_name': 'waveform'
    }
    targetfile = os.path.expanduser(targetfile)
    waveform_launcher.launch(args)
    dat = pkl_sig_format.WaveformPklReader(targetfile)
    x = dat.read_section()
    plt.plot(np.abs(x))
    plt.show()
    os.remove(targetfile)

