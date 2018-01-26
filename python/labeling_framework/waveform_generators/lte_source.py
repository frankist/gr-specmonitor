#!/usr/bin/env python

import numpy as np
import os
import pickle
import time
import sys
import matplotlib.pyplot as plt

from gnuradio import gr
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes

# labeling_framework package
import specmonitor
from waveform_generator_utils import *
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class GrLTETracesFlowgraph(gr.top_block):
    # NOTE: srsLTE does not use the standard mapping
    # prb_mapping = {"06": 128, "15": 256, "25": 512,
    #                "50": 1024, "75": 1536, "100": 2048}
    #fftsize_mapping = {128: 1.4e6, 256: 3e6, 512: 5.0e6, 1024: 10.0e6, 1536: 15.0e6, 2048: 20.0e6}
    prb_mapping = {6: 128, 15: 256, 25: 384, 50: 768, 75: 1024, 100: 1536}
    fftsize_mapping = {128: 1.4e6, 256: 3e6, 384: 5.0e6, 768: 10.0e6, 1024: 15.0e6, 1536: 20.0e6}
    def __init__(self,n_samples,
                 n_offset_samples,
                 n_prbs,
                 linear_gain,
                 pad_interval,
                 mcs,
                 frequency_offset):
        super(GrLTETracesFlowgraph, self).__init__()
        self.subcarrier_spacing = 15000

        # params
        self.n_samples = n_samples
        self.n_prbs = n_prbs
        self.linear_gain = linear_gain
        self.mcs = mcs

        # derived params
        if isinstance(n_offset_samples,tuple):
            if n_offset_samples[0]=='uniform':
                self.n_offset_samples = np.random.randint(*n_offset_samples[1])
            else:
                raise NotImplementedError('I don\'t recognize this.')
        else:
            self.n_offset_samples = int(n_offset_samples)
        if isinstance(pad_interval,tuple):
            self.pad_interval = pad_interval[1]
            self.pad_dist = pad_interval[0]
        else:
            self.pad_interval = [pad_interval]
            self.pad_dist = 'constant'
        if isinstance(frequency_offset,tuple):
            assert frequency_offset[0]=='uniform'
            self.frequency_offset = frequency_offset[1]
        else: # it is just a value
            self.frequency_offset = [frequency_offset]
        self.fft_size = GrLTETracesFlowgraph.prb_mapping[self.n_prbs]
        self.samp_rate = float(self.fft_size*self.subcarrier_spacing)
        frames_path = os.path.expanduser('~/tmp/lte_frames')
        n_prbs_str = "%02d" % (self.n_prbs,)
        mcs_str = "%02d" % (self.mcs)
        fname = '{}/lte_dump_prb_{}_mcs_{}.32fc'.format(frames_path,n_prbs_str,mcs_str)
        self.expected_bw = GrLTETracesFlowgraph.fftsize_mapping[self.fft_size]
        self.resamp_ratio = 20.0e6/self.samp_rate
        self.n_samples_per_frame = int(10.0e-3*self.samp_rate)

        # blocks
        # print 'this is the filename:',fname
        self.file_reader = blocks.file_source(gr.sizeof_gr_complex,fname,True)
        self.tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,self.n_samples_per_frame,"packet_len")
        self.burst_shaper = specmonitor.random_burst_shaper_cc(self.pad_dist, self.pad_interval, 0, self.frequency_offset,"packet_len")
        # self.resampler = filter.rational_resampler_base_ccc(interp,decim,taps)
        self.resampler = filter.fractional_resampler_cc(0,1/self.resamp_ratio)
        self.skiphead = blocks.skiphead(gr.sizeof_gr_complex,
                                        self.n_offset_samples)
        self.head = blocks.head(gr.sizeof_gr_complex, self.n_samples)
        self.dst = blocks.vector_sink_c()

        self.setup_flowgraph()

    def setup_flowgraph(self):
        ##################################################
        # Connections
        ##################################################
        self.connect(self.file_reader, self.tagger)
        self.connect(self.tagger, self.burst_shaper)
        self.connect(self.burst_shaper, self.resampler)
        self.connect(self.resampler, self.skiphead)
        self.connect(self.skiphead, self.head)
        self.connect(self.head, self.dst)

    def run(self): # There is some bug with this gr version when I use streams
        self.start()
        while self.dst.nitems_read(0) < self.n_samples:
            time.sleep(0.01)
        self.stop()
        self.wait()

    @classmethod
    def load_flowgraph(cls,params):
        n_samples = int(params['n_samples'])
        n_offset_samples = params.get('n_offset_samples',0)
        n_prbs = int(params['n_prbs'])
        linear_gain = float(params.get('linear_gain',1.0))
        pad_interval = params['pad_interval']
        mcs = np.random.randint(0,28)
        frequency_offset = params.get('frequency_offset',0.0)
        return cls(n_samples, n_offset_samples, n_prbs, linear_gain, pad_interval, mcs, frequency_offset)

def run(args):
    d = args['parameters']
    print_params(d,__name__)

    while True:
        # create general_mod block
        tb = GrLTETracesFlowgraph.load_flowgraph(d)

        logger.info('Starting GR waveform generator script for LTE')
        tb.run()
        logger.info('GR script finished')

        gen_data = np.array(tb.dst.data())

        try:
            v = transform_IQ_to_sig_data(gen_data,args)
        except RuntimeError, e:
            logger.warning('Going to re-run radio')
            continue
        break

    # save file
    fname = os.path.expanduser(args['targetfilename'])
    with open(fname, 'w') as f:
        pickle.dump(v, f)
    logger.debug('Finished writing to file %s', fname)
