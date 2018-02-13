#!/usr/bin/env python

import numpy as np
import os
# import pickle
import cPickle as pickle
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
from specmonitor import random_burst_shaper_cc
from specmonitor import labeling_framework as lf
from specmonitor.labeling_framework.waveform_generators import waveform_generator_utils as wav_utils
from specmonitor.labeling_framework import timefreq_box as tfbox
from specmonitor.labeling_framework.labeling_tools import random_sequence
logger = lf.DynamicLogger(__name__)

class GrLTEULTracesFlowgraph(gr.top_block):
    prb_mapping = {6: 128, 15: 256, 25: 384, 50: 768, 75: 1024, 100: 1536}
    fftsize_mapping = {128: 1.4e6, 256: 3e6, 384: 5.0e6, 768: 10.0e6, 1024: 15.0e6, 1536: 20.0e6}
    lte_up_filenames = ['ul_p_50_d_1.32fc', 'ul_p_50_d_2.32fc', 'ul_p_50_d_3.32fc', 'ul_p_50_d_6.32fc']
    def __init__(self,n_samples,
                 n_offset_samples,
                 linear_gain,
                 pad_interval,
                 frequency_offset):
        super(GrLTEULTracesFlowgraph, self).__init__()

        # params
        self.n_samples = n_samples
        self.n_offset_samples = int(lf.random_generator.load_value(n_offset_samples))
        self.linear_gain = linear_gain
        trace_number = 0

        #derived
        subcarrier_spacing = 15000
        fftsize = GrLTEULTracesFlowgraph.prb_mapping[50]
        self.samp_rate = float(fftsize*subcarrier_spacing)
        self.expected_bw = GrLTEULTracesFlowgraph.fftsize_mapping[fftsize]
        self.fname = GrLTEULTracesFlowgraph.lte_up_filenames[trace_number]
        self.fname = os.path.expanduser(os.path.join('~/tmp/lte_frames/ul',self.fname))
        self.n_samples_per_frame = int(10.0e-3*self.samp_rate)
        self.resamp_ratio = 20.0e6/self.samp_rate
        randgen = lf.random_generator.load_generator(pad_interval)
        # scale by sampling rate
        new_params = [int(v/self.resamp_ratio) for v in randgen.params]
        randgen = lf.random_generator(randgen.dist_name,new_params)

        if isinstance(frequency_offset,tuple):
            assert frequency_offset[0]=='uniform'
            self.frequency_offset = frequency_offset[1]
        else: # it is just a value
            self.frequency_offset = [frequency_offset]

        # blocks
        self.file_reader = blocks.file_source(gr.sizeof_gr_complex,self.fname,True)
        self.tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,self.n_samples_per_frame,"packet_len")
        self.burst_shaper = random_burst_shaper_cc(randgen.dynrandom(), 0, self.frequency_offset,"packet_len")
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
        # self.connect(self.burst_shaper, self.skiphead)
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
        frequency_offset = params.get('frequency_offset',0.0)
        return cls(n_samples, n_offset_samples, linear_gain, pad_interval, frequency_offset)

def run(args):
    d = args['parameters']
    # print_params(d,__name__)

    # create general_mod block
    tb = GrLTEULTracesFlowgraph.load_flowgraph(d)

    logger.info('Starting GR waveform generator script for LTE')
    tb.run()
    logger.info('GR script finished')

    # output signal
    x = np.array(tb.dst.data())

    # create a StageSignalData structure
    stage_data = wav_utils.set_derived_sigdata(x,args,True)
    metadata = stage_data.derived_params['spectrogram_img']
    tfreq_boxes = metadata.tfreq_boxes
    tfbox.set_boxes_mag2(x,tfreq_boxes)

    # set static/pre-defined bandwidth
    frac_bw = tb.expected_bw/20.0e6
    freq_tuple = (-frac_bw/2,frac_bw/2)
    for b in tfreq_boxes:
        tfreq_boxes[i].freq_bounds = freq_tuple

    # randomly scale and normalize boxes magnitude
    frame_mag2_gen = lf.random_generator.load_generator(args['parameters'].get('frame_mag2',1))
    tfreq_boxes = wav_utils.random_scale_mag2(tfreq_boxes,frame_mag2_gen)
    tfreq_boxes = wav_utils.normalize_mag2(tfreq_boxes)
    y = wav_utils.set_signal_mag2(x,tfreq_boxes)
    metadata.tfreq_boxes = tfreq_boxes
    stage_data.samples = y

    # create a MultiStageSignalData structure and save it
    v = lf.MultiStageSignalData()
    v.set_stage_data(stage_data)
    v.save_pkl()

class LTEULGenerator(lf.SignalGenerator):
    @staticmethod
    def run(params):
        while True:
            try:
                run(params)
            except RuntimeError, e:
                logger.warning('Failed to generate the waveform data for WiFi. Going to rerun. Arguments: {}'.format(args))
                continue
            except KeyError, e:
                logger.error('The input arguments do not seem valid. They were {}'.format(args))
                raise
            break

    @staticmethod
    def name():
        return 'lte_ul'

if __name__=='__main__':
    d = {'n_samples':1000000,'n_offset_samples':100,'pad_interval':100000}
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
