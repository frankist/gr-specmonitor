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

from specmonitor import spectrogram_img_c
from specmonitor import darkflow_ckpt_classifier_msg

class DarkflowFlowGraph(gr.top_block):
    def __init__(self,yaml_config=''):
        super(DarkflowFlowGraph, self).__init__()

        # params
        self.yaml_config = yaml_config
        sample_rate = 20.0e6
        centre_freq = 2.35e9#3.5e9
        gaindB = 10#30
        fftsize = 104
        n_avgs = 80

        # flowgraph blocks
        self.usrp_source = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.usrp_source.set_samp_rate(sample_rate)
        self.usrp_source.set_center_freq(centre_freq,0)
        self.usrp_source.set_gain(gaindB,0)
        self.toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, fftsize)
        self.fftblock = fft.fft_vcc(fftsize,True,signal.get_window(('tukey',0.25),fftsize),True)
        self.spectroblock = spectrogram_img_c(fftsize,104,104,n_avgs,True)
        self.classifier = darkflow_ckpt_classifier_msg(self.yaml_config, fftsize, 0.6)

        # make flowgraph
        self.connect(self.usrp_source,self.toparallel)
        self.connect(self.toparallel,self.fftblock)
        self.connect(self.fftblock,self.spectroblock)
        self.msg_connect(self.spectroblock, "imgcv", self.classifier, "gray_img")

    # def run(self):
    #     # GNURadio has some bug when using streams. It hangs
    #     self.run()
    #     # self.tb.start()
    #     # self.stop()
    #     # self.wait()
    #     # yolo_result = classifier.last_result

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Setup the files for training/testing')
    parser.add_argument('--config', type=str,
                        help='YAML file for config', required=True)
    args = parser.parse_args()

    tb = DarkflowFlowGraph(args.config)
    tb.run()
