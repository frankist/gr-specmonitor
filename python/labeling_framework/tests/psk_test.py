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

# load labeling_framework package
import sys
import os
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# load file to test
from waveform_generators.psk_source import *
from sig_format import pkl_sig_format

if __name__ == '__main__':
    logging.basicConfig(level='DEBUG')
    targetfile = '~/tmp/out.pkl'
    args = {
        'parameters': {
            'number_samples': 100000,
            'waveform':'generic_mod',
            'constellation':'psk',
            'order':4,
            'mod_code':'GRAY',
            'differential':False,
            'samples_per_symbol':10,
            'excess_bw':0.25,
            'pre_diff_code':False,
            'burst_len':5000,
            'zero_pad_len':5000,
        },
        'targetfilename': targetfile,
        'stage_name': 'waveform'
    }
    targetfile = os.path.expanduser(targetfile)
    run(args)
    dat = pkl_sig_format.WaveformPklReader(targetfile)
    x = dat.read_section()
    plt.plot(np.abs(x))
    plt.show()
    os.remove(targetfile)

