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
from gnuradio import gr
from gnuradio import blocks
from gnuradio import uhd
import pickle
import json
import os

def run_RF_Rx_on_repeat(outputfile,params,sample_rate,n_rx_samples,n_skip_samples):
    ### Set variables based on given stage parameters
    gaindB = params['rx_gaindB']
    centre_freq = params['rf_frequency']

    print 'STATUS: Going to store',n_rx_samples, 'samples. Going to skip',n_skip_samples

    tb = gr.top_block()
    usrp_source = uhd.usrp_source(
        ",".join(("", "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    usrp_source.set_samp_rate(sample_rate)
    usrp_source.set_center_freq(centre_freq,0)
    usrp_source.set_gain(gaindB,0)
    skip = blocks.skiphead(gr.sizeof_gr_complex,n_skip_samples)
    head = blocks.head(gr.sizeof_gr_complex,n_rx_samples)
    fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

    tb.connect(usrp_source,skip)
    tb.connect(skip,head)
    tb.connect(head,fsink)

    tb.run()

if __name__ == '__main__':
    json_file = sys.argv[1]
    with open(json_file,'r') as f:
        jsonparams = json.load(f)
    outputfile = str(os.path.expanduser(jsonparams['outputfile']))
    params = jsonparams['params']
    sample_rate = jsonparams['sample_rate']
    n_rx_samples = jsonparams['n_rx_samples']
    n_skip_samples = jsonparams['n_skip_samples']
    run_RF_Rx_on_repeat(outputfile,params,sample_rate,n_rx_samples,n_skip_samples)