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
import os
import time
from gnuradio import gr
from gnuradio import blocks
import specmonitor as specmonitor
import zadoffchu
import numpy as np
import json
import argparse

class sim_awgn:
    def __init__(self):
        self.samples_per_rx = 64*64*15
        self.samples_per_frame = self.samples_per_rx + 1000
        self.num_frames = 10

    def generate_waveform_file(f_batch):
        # we don't care about the snr or any other channel effect here
        tb = gr.top_block()

        # generate preamble

        # waveform->framer->filesink
        # run

        # generate the tags associated with this file (keep the original to be read by a filesink)

    def generate_rx_files(f_batch):
        tb = gr.top_block()

        # generate preamble

        # filesink->channel->crossdetector->null
        # if frames were found
        #    write multiple subfiles, each for each frame
        #    write also the tags
        # else:
        #    rerun

        # NOTE: In the case of OTT, I cannot just re-run the crossdetector. I need to re-generate the waveform again
        #       To sort that out, I have to erase the current f_batch, and re-run its tag in the makefile. I need to print that filename to the makefile environment. I can do this by returning an error from this python script and then if error, call f_batch as a target

    # set waveform->framer->channel->filesink (do I really need gnuradio for this? Yes, bc over-the-air you may need to change the freq. of the USRP in real time)
    # run
    # NOTE: this phase does not depend on SNR. Should we do it separately?

    # if we were doing over the air we could just filesink->USRP (what about the USRP freq and gain?)

    # set filesource->crosscorr
    # read the tags of crosscorr and write multiple pkl files (each file for each frame)

if __name__ == '__main__':
    # parse the arguments
    # waveform=
    # snr=
    # batch=
    test(waveform,snr,batch)
    pass
