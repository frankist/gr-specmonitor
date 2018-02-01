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
import os
import pickle
import time
import types
# import matplotlib.pyplot as plt

# gnuradio dependencies
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
import specmonitor

# labeling_framework package
from waveform_generator_utils import *
from ..utils import typesystem_utils as ts
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def make_constellation_object(params):
    gr_params = {}
    constellation_str = params['constellation']
    gr_params['m'] = params['order']
    gr_params['differential'] = params.get('differential',False) # give it a default
    mod_code_str = params.get('mod_code','GRAY')
    if mod_code_str=='GRAY' or mod_code_str=='gray':
        gr_params['mod_code'] = digital.mod_codes.GRAY_CODE
    elif mod_code_str=='no_code' or mod_code_str=='NO_CODE':
        gr_params['mod_code'] = digital.mod_codes.NO_CODE
    else:
        logger.error('The provided mod code for the generic modulator is not recognized')
        raise AttributeError('I do not recognize this mod_code')
    logger.debug('these are the params %s', gr_params)
    if constellation_str=='psk':
        return digital.psk_constellation(**gr_params)
    elif constellation_str=='qam':
        return digital.qam_constellation(**gr_params)
    else:
        logger.error('The provided constellation is not supported')
        raise AttributeError('I do not recognize this constellation')

class GeneralModFlowgraph(gr.top_block):
    def __init__(self,
                 n_written_samples,
                 constellation_obj,
                 #pre_diff_code,
                 samples_per_symbol,
                 excess_bw,
                 burst_len,
                 zero_pad_len,
                 linear_gain=1.0,
                 frequency_offset=0.0):
        super(GeneralModFlowgraph, self).__init__()

        # params
        self.n_written_samples = int(n_written_samples)
        self.n_offset_samples = int(np.random.randint(0,self.n_written_samples))
        self.constellation_obj = constellation_obj
        self.samples_per_symbol = samples_per_symbol #TODO
        self.excess_bw = excess_bw # TODO
        self.linear_gain = float(linear_gain)
        self.burst_len = burst_len
        # TODO: make burst_len also variable
        if isinstance(zero_pad_len,tuple):
            self.zero_pad_len = zero_pad_len[1]
            self.pad_dist = zero_pad_len[0]
        else:
            self.zero_pad_len = [zero_pad_len]
            self.pad_dist = 'constant'
        if isinstance(frequency_offset,tuple):
            assert frequency_offset[0]=='uniform'
            self.frequency_offset = frequency_offset[1]
        else: # it is just a value
            self.frequency_offset = [frequency_offset]
        # print 'This is the frequency offset:',frequency_offset
        # self.burst_len = burst_len if not issubclass(burst_len.__class__,ts.ValueGenerator) else burst_len.generate()
        # self.zero_pad_len = zero_pad_len  if not issubclass(zero_pad_len.__class__,ts.ValueGenerator) else zero_pad_len.generate()
        data2send = np.random.randint(0,256,1000)

        # phy
        self.data_gen = blocks.vector_source_b(data2send,True)
        self.mod = digital.generic_mod(self.constellation_obj,
                                       samples_per_symbol=self.samples_per_symbol,
                                       #self.pre_diff_code,
                                       excess_bw=self.excess_bw)
        self.tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,self.burst_len,"packet_len")
        # self.burst_shaper = digital.burst_shaper_cc((1+0*1j,),100,self.zero_pad_len,False)
        self.burst_shaper = specmonitor.random_burst_shaper_cc(self.pad_dist,self.zero_pad_len,0,self.frequency_offset,"packet_len")
        self.skiphead = blocks.skiphead(gr.sizeof_gr_complex, self.n_offset_samples)
        self.head = blocks.head(gr.sizeof_gr_complex, self.n_written_samples)
        self.dst = blocks.vector_sink_c()
        # dst = blocks.file_sink(gr.sizeof_gr_complex,args['targetfolder']+'/tmp.bin')

        self.setup_flowgraph()

    def setup_flowgraph(self):
        ##################################################
        # Connections
        ##################################################
        self.connect(self.data_gen, self.mod)
        self.connect(self.mod, self.tagger)
        self.connect(self.tagger, self.burst_shaper)
        self.connect(self.burst_shaper, self.skiphead)
        self.connect(self.skiphead, self.head)
        self.connect(self.head, self.dst)

    def run(self): # There is some bug with this gr version when I use streams
        self.start()
        while self.dst.nitems_read(0) < self.n_written_samples:
            time.sleep(0.01)
        self.stop()
        self.wait()

    @classmethod
    def load_flowgraph(cls,params):
        n_written_samples = int(params['number_samples'])
        constellation_obj = make_constellation_object(params)
        samples_per_symbol = params['samples_per_symbol']
        # pre_diff_code =
        excess_bw = params['excess_bw']
        zero_pad_len = params['zero_pad_len']
        burst_len = params['burst_len']
        frequency_offset = params.get('frequency_offset',0)
        return cls(n_written_samples,constellation_obj,samples_per_symbol,excess_bw,burst_len,zero_pad_len,linear_gain=1.0,frequency_offset=frequency_offset)

def create_multiple_Txs(params):
    tb_list = []
    freq_param = params.get('frequency_offset',[0])
    if isinstance(freq_param,tuple) and freq_param[0]=='multipleTx':
        for freq in freq_param[1]:
            params2 = dict(params)
            params2['frequency_offset'] = freq
            tb_list.append(GeneralModFlowgraph.load_flowgraph(params2))
    else:
        tb_list.append(GeneralModFlowgraph.load_flowgraph(d))
    return tb_list

def run(args):
    d = args['parameters']
    print_params(d,__name__)

    # create general_mod block
    # tb = GeneralModFlowgraph.load_flowgraph(d)
    tb_list = create_multiple_Txs(d)

    waveform_data_list = []
    for tb in tb_list:
        while True:
            logger.info('Starting GR waveform generator script for PSK')
            tb.run()
            logger.info('GR script finished')

            gen_data = np.array(tb.dst.data())

            try:
                v = transform_IQ_to_sig_data(gen_data,args)
            except RuntimeError, e:
                logger.warning('Going to re-run radio')
                continue
            waveform_data_list.append(v)
            break
    v = aggregate_independent_waveforms(waveform_data_list)

    # aggregate everything
    v.save_pkl()
    # logger.debug('Finished writing to file %s', fname)
