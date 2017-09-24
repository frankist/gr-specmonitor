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

# class sim_awgn:
#     def __init__(self):
#         self.samples_per_rx = 64*64*15
#         self.samples_per_frame = self.samples_per_rx + 1000
#         self.num_frames = 10

#     def generate_batch_file(f_batch):
#         # we don't care about the snr or any other channel effect here
#         tb = gr.top_block()

#         # generate preamble

#         # waveform->framer->filesink
#         # run

#         # generate the tags associated with this file (keep the original to be read by a filesink)

#     def generate_rx_files(f_batch):
#         tb = gr.top_block()

#         # generate preamble

#         # filesink->channel->crossdetector->null
#         # if frames were found
#         #    write multiple subfiles, each for each frame
#         #    write also the tags
#         # else:
#         #    rerun

#         # NOTE: In the case of OTT, I cannot just re-run the crossdetector. I need to re-generate the waveform again
#         #       To sort that out, I have to erase the current f_batch, and re-run its tag in the makefile. I need to print that filename to the makefile environment. I can do this by returning an error from this python script and then if error, call f_batch as a target

#     # set waveform->framer->channel->filesink (do I really need gnuradio for this? Yes, bc over-the-air you may need to change the freq. of the USRP in real time)
#     # run
#     # NOTE: this phase does not depend on SNR. Should we do it separately?

#     # if we were doing over the air we could just filesink->USRP (what about the USRP freq and gain?)

#     # set filesource->crosscorr
#     # read the tags of crosscorr and write multiple pkl files (each file for each frame)

def write_batch_file(self, batch_filename, params):
    pass

def interval_intersect(t1,t2):
    return (t1[0]>=t2[0] and t1[0]<t2[1]) or (t1[1]>=t2[0] and t1[1]<t2[1])

class WaveformFilePartitioner:
    def __init__(self, waveform_reader, section_size, n_sections_per_batch, section_step = None):
        self.waveform_reader = waveform_reader
        self.section_size = section_size
        self.n_sections = n_sections_per_batch
        self.section_step = section_step if section_step is not None else section_size
        self.metadata = self.waveform_reader.metatadata()
        self.bounding_boxes = self.metadata.pop('bounding_boxes') # self.metadata does not contain boxes

    def generate_section(self,section_idx):
        win_range = (section_idx*self.section_step,section_idx*self.section_step+self.section_size)
        boxes_of_interest = [(a['start']-win_range[0],a['end']-win_range[0]) for a in self.bounding_boxes if interval_intersect((a['start'],a['end']),win_range)]
        # NOTE: this search can be optimized
        if win_range[1] <= self.waveform_reader.size():
            samples = self.waveform_reader.read_section(win_range[0],win_range[1])
        else:
            raise ValueError('Section index went beyond file bounds')
        return {'bounding_boxes':boxes_of_interest,'IQsamples':samples}

    def generate_batch(self,batch_idx):
        first_section = batch_idx*self.n_sections
        batch = {'metadata':self.metadata, 'sections':[]}

        for i in range(self.n_sections):
            d = self.generate_section(first_section+i)
            batch['sections'].append(d)

        return batch

# This will create several batches for:
# -> different time indexes of the original waveformfile
# -> different permutations over tx_params

def generate_and_write_tx_batches(waveform_idx, meta_file, batch_idxs=None):
    tx_stage_idx = metadata_handling.stage_names.index('Tx')
    wv_stage_idx = metadata_handling.stage_names.index('waveform')
    meta_manager = metadata_handling.get_handler() # FIXME

    txparams = meta_manager.possible_stage_values(stage_idx)
    section_size = txparams['section_size']
    n_sections_per_batch = txparams['n_sections_per_batch']

    batch_gen = WaveformFilePartitioner(WaveformPklReader(wav_filename), section_size, n_sections_per_batch, 5)
    batch_param_entries = meta_manager.stage_entries(tx_stage_idx,batch_idxs)
    for i,p in enumerate(batch_param_entries):
        txbatch = batch_gen.generate_batch(batch_idxs[0]+i)
        # apply other transforms here
        txbatch = transform(txbatch,p)
        fname = metadata_handling.get_filename(tx_stage_idx,[waveform_idx,batch_idxs[i]])
        pickle.dumps(fname,txbatch)

if __name__ == '__main__':
    # parse the arguments
    # waveform_file=
    # snr=
    # batch=
    test(waveform,snr,batch)
    pass
