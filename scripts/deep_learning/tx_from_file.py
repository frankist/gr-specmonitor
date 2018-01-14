#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2018 <+YOU OR YOUR COMPANY+>.
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

from gnuradio import gr
from gnuradio import blocks
from gnuradio import fft
from gnuradio import uhd
import numpy as np
import cv2
import os
import sys
from scipy import signal
import argparse

sys.path.append('../../python/')
from labeling_framework.sig_format import pkl_sig_format
from labeling_framework.sig_format import sig_data_access as sda

class TxFromFile(gr.top_block):
    def __init__(self,pkl_file):
        super(TxFromFile, self).__init__()

        # params
        # TODO: make reading from yaml
        sample_rate = 20.0e6
        centre_freq = 3.5e9
        gaindB = 20

        # write pickle to raw fc32
        # tmp_path = os.path.join(os.path.dirname(os.path.dirname(pkl_file)),'tmp')
        # tmp_filename = os.path.join(tmp_path,'tmp_tx.32fc')
        freader = pkl_sig_format.WaveformPklReader(pkl_file)
        x = freader.read_section()
        stage_data = freader.data()
        spec_metadata = sda.get_stage_derived_parameter(stage_data,'section_spectrogram_img_metadata')
        section_bounds = spec_metadata[0].section_bounds
        xsection = x[section_bounds[0]:section_bounds[1]]
        xtuple = tuple([complex(i) for i in xsection])

        # flowgraph blocks
        self.vector_source = blocks.vector_source_c(xtuple, True)
        self.usrp_sink = uhd.usrp_sink(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.usrp_sink.set_samp_rate(sample_rate)
        self.usrp_sink.set_center_freq(centre_freq,0)
        self.usrp_sink.set_gain(gaindB,0)

        # make flowgraph
        self.connect(self.vector_source,self.usrp_sink)

if __name__=='__main__':
    dataset_path_default = '../ota/awgn/sim0/Tx/'
    parser = argparse.ArgumentParser(description='Setup the files for training/testing')
    parser.add_argument('--file', type=str,
                        help='file that is going to be transmitted over the air', required=True)
    parser.add_argument('--dataset', type=str, default=dataset_path_default,
                        help='file that is going to be transmitted over the air', required=False)
    args = parser.parse_args()

    pkl_file = os.path.join(args.dataset,args.file)
    pkl_file = os.path.abspath(os.path.expanduser(pkl_file))
    tb = TxFromFile(pkl_file)
    tb.run()
