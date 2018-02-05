#!/usr/bin/env python

import numpy as np
import os
import pickle
import time
import sys
import matplotlib.pyplot as plt
import scipy
import copy

from gnuradio import gr
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes

# labeling_framework package
import specmonitor
from labeling_framework.core import session_settings
from labeling_framework.waveform_generators.waveform_generator_utils import *
from labeling_framework.labeling_tools import random_sequence
from labeling_framework.data_representation import timefreq_box as tfbox
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class GrLTEULTracesFlowgraph(gr.top_block):
    lte_up_filenames = ['ul_p_50_d_1.32fc', 'ul_p_50_d_2.32fc', 'ul_p_50_d_3.32fc', 'ul_p_50_d_6.32fc']
    def __init__(self,n_samples,
                 n_offset_samples,
                 trace_number,
                 linear_gain,
                 pad_interval,
                 frequency_offset):
        super(GrLTEULTracesFlowgraph, self).__init__()

        # params
        self.n_samples = n_samples
        self.linear_gain = linear_gain

        self.samp_rate = 20e6
        self.fname = GrLTEULTracesFlowgraph.lte_up_filenames[trace_number]
        self.fname = os.path.expanduser(os.path.join('~/tmp/lte_frames/ul',self.fname))
        self.n_samples_per_frame = int(10.0e-3*self.samp_rate)

        # # derived params
        # frames_path = os.path.expanduser('~/tmp/lteshell_frames/ul')
        # self.expected_bw = GrLTEULTracesFlowgraph.fftsize_mapping[self.fft_size]
        self.resamp_ratio = 20.0e6/self.samp_rate
        # self.n_samples_per_frame = int(10.0e-3*self.samp_rate)
        if isinstance(n_offset_samples,tuple):
            if n_offset_samples[0]=='uniform':
                self.n_offset_samples = np.random.randint(*n_offset_samples[1])
            else:
                raise NotImplementedError('I don\'t recognize this.')
        else:
            self.n_offset_samples = int(n_offset_samples)
        if isinstance(pad_interval,tuple):
            self.pad_interval = [int(p/self.resamp_ratio) for p in pad_interval[1]]
            self.pad_dist = pad_interval[0]
        else:
            self.pad_interval = [int(pad_interval/self.resamp_ratio)]
            self.pad_dist = 'constant'
        if isinstance(frequency_offset,tuple):
            assert frequency_offset[0]=='uniform'
            self.frequency_offset = frequency_offset[1]
        else: # it is just a value
            self.frequency_offset = [frequency_offset]

        print 'file name is :', self.fname
        # blocks
        self.file_reader = blocks.file_source(gr.sizeof_gr_complex,self.fname,True)
        self.tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,self.n_samples_per_frame,"packet_len")
        self.burst_shaper = specmonitor.random_burst_shaper_cc(self.pad_dist, self.pad_interval, 0, self.frequency_offset,"packet_len")
        # self.resampler = filter.fractional_resampler_cc(0,1/self.resamp_ratio)
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
        # self.connect(self.burst_shaper, self.resampler)
        # self.connect(self.resampler, self.skiphead)
        self.connect(self.burst_shaper, self.skiphead)
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
        linear_gain = float(params.get('linear_gain',1.0))
        pad_interval = params['pad_interval']
        trace_number = params.get('trace_number',np.random.randint(0,len(GrLTEULTracesFlowgraph.lte_up_filenames)))
        frequency_offset = params.get('frequency_offset',0.0)
        return cls(n_samples, n_offset_samples, trace_number, linear_gain, pad_interval, frequency_offset)

def run(args):
    d = args['parameters']
    print_params(d,__name__)

    while True:
        # create general_mod block
        tb = GrLTEULTracesFlowgraph.load_flowgraph(d)

        logger.info('Starting GR waveform generator script for LTE')
        tb.run()
        logger.info('GR script finished')

        gen_data = np.array(tb.dst.data())

        try:
            v = transform_IQ_to_sig_data(gen_data,args)

            # merge boxes if broadcast channel is empty
            metadata = v.get_stage_derived_params('spectrogram_img')
            # tfreq_boxes = copy.deepcopy(metadata.tfreq_boxes)
            # new_tfreq_boxes = merge_boxes_within_same_lte_frame(gen_data,
            #     tfreq_boxes,tb.fft_size)
            # metadata.tfreq_boxes = new_tfreq_boxes
            # # NOTE: being a Ptr, it should be stored in the multi_stage_data
        except RuntimeError, e:
            logger.warning('Going to re-run radio')
            continue
        break

    # save file
    v.save_pkl()

class LTEULGenerator(SignalGenerator):
    @staticmethod
    def run(params):
        run(params)
    @staticmethod
    def name():
        return 'lte_ul'

if __name__=='__main__':
    d = {'n_samples':1000000,'n_offset_samples':100,'pad_interval':100000, 'trace_number':1}
    tb = GrLTEULTracesFlowgraph.load_flowgraph(d)
    tb.run()
    xout = np.array(tb.dst.data())

    from labeling_framework.data_representation import spectrogram

    Sxx = spectrogram.compute_spectrogram(xout,1024)
    X = np.fft.fftshift(np.abs(np.fft.fft(xout)))
    # plt.imshow(Sxx)
    # plt.plot(X)
    # plt.plot(np.abs(xout))
    Pxx, freqs, bins, im = plt.specgram(xout,NFFT=1024,Fs=20e6,noverlap=100,cmap=plt.cm.gist_heat)
    plt.show()
