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
import specmonitor
from specmonitor import labeling_framework as lf
from specmonitor.labeling_framework.waveform_generators import waveform_generator_utils as wav_utils
from specmonitor.labeling_framework import timefreq_box as tfbox
from specmonitor.labeling_framework.labeling_tools import random_sequence
logger = lf.DynamicLogger(__name__)

prb_mapping = {6: 128, 15: 256, 25: 384, 50: 768, 75: 1024, 100: 1536}
fftsize_mapping = {128: 1.4e6, 256: 3e6, 384: 5.0e6, 768: 10.0e6, 1024: 15.0e6, 1536: 20.0e6}
ZC_cached = {}
bw_cached = {}

def compute_LTE_ZC(fft_size):
    if fft_size in ZC_cached:
        return ZC_cached[fft_size]
    subcarrier_spacing=15000
    LTE_samp_rate = float(fft_size*subcarrier_spacing)
    resamp_ratio = 20.0e6/LTE_samp_rate
    zc = random_sequence.zadoffchu_freq_noDC_sequence(63,25,0,fft_size)
    zc_resampled = scipy.signal.resample(zc,int(len(zc)*resamp_ratio))
    ZC_cached[fft_size] = zc_resampled
    return zc_resampled

def find_zc_peaks(x,fft_size):
    zc = compute_LTE_ZC(fft_size)
    xcorr = np.correlate(x,zc)
    xcorrabs = np.abs(xcorr)/np.max(np.abs(xcorr))
    peaks = np.where(xcorrabs>0.8)[0]
    peaks_sorted = peaks[np.argsort(xcorrabs[peaks])]
    max_peaks = []
    while len(peaks_sorted)>0:
        max_peaks.append(peaks_sorted[-1])
        peaks_sorted = [p for p in peaks_sorted if np.abs(peaks_sorted[-1]-p)>fft_size]
    max_peaks = np.sort(max_peaks)
    return max_peaks

def lte_frame_window(peak,samp_rate):
    frame_dur=10.0e-3*samp_rate
    pss_offset = int(np.round(406.9e-6*samp_rate))
    return (peak-pss_offset,peak+frame_dur-pss_offset)

def find_lte_frame_windows(x,fft_size):
    l = []
    half_frame_dur=5.0e-3*20.0e6+1
    peaks = find_zc_peaks(x,fft_size)
    peaks_remaining = np.copy(peaks)
    while len(peaks_remaining)>0:
        p = peaks_remaining[0]
        p2_list = np.where(np.abs(p+half_frame_dur-peaks_remaining[1::])<2)[0]
        if len(p2_list)>0: # we found the second peak
            assert len(p2_list)==1
            l.append(lte_frame_window(p,20.0e6))#samp_rate
            peaks_remaining = np.delete(peaks_remaining,[0,1+p2_list[0]])
        else:
            if p>=len(x)-half_frame_dur: # at the right border. the frame was not complete
                l.append(lte_frame_window(p,20.0e6))
                peaks_remaining = np.delete(peaks_remaining,[0])
            elif p<=half_frame_dur: # at the left border. we missed the start of the frame
                l.append(lte_frame_window(p-int(20.0e6*5.0e-3),20.0e6))
                peaks_remaining = np.delete(peaks_remaining,[0])
            else:
                raise RuntimeError('Couldnt find the second PSSS peak of the LTE frame')
    return l

def merge_boxes_within_same_lte_frame(x,tfreq_boxes_x,fft_size):
    tfreq_boxes = copy.deepcopy(tfreq_boxes_x)
    frame_win_list = find_lte_frame_windows(x,fft_size)
    if len(frame_win_list)==0:
        raise RuntimeError('Couldnt find any ZC peak')
    new_tfreq_boxes = []
    # NOTE: This avoids eliminating boxes for which frames were not found.
    # They are considered last, so there are no common boxes between them and other frames
    begin_truncate = (0,frame_win_list[0][0])
    end_truncate = (frame_win_list[-1][1]+1,len(x))
    frame_win_list.append(begin_truncate)
    frame_win_list.append(end_truncate) # this includes boxes for which frame was not found
    for tframe in frame_win_list:
        frame_boxes = list(tfbox.select_boxes_that_intersect_section(tfreq_boxes,tframe))
        if len(frame_boxes)==0:
            continue
        maxpwr = np.max([b.params['power'] for b in frame_boxes])
        mintstamp = np.min([b.time_bounds[0] for b in frame_boxes])
        maxtstamp = np.max([b.time_bounds[1] for b in frame_boxes])
        minfreq = np.min([b.freq_bounds[0] for b in frame_boxes])
        maxfreq = np.max([b.freq_bounds[1] for b in frame_boxes])
        # caches the measured BW. If we capture a box that does not fit this BW
        # (CC may have smaller BW), we correct it
        if np.abs(maxfreq+minfreq)>0.01:#1e-5: # I do not expect CFO here
            raise AssertionError('I do not expect CFO here. However, I got ({},{})'.format(minfreq,maxfreq))
        if fft_size not in bw_cached or (maxfreq-minfreq)>(bw_cached[fft_size][1]-bw_cached[fft_size][0]):
            bw_cached[fft_size] = (minfreq,maxfreq)
        minfreq,maxfreq = bw_cached[fft_size]
        if tframe!=begin_truncate:
            maxtstamp = max(maxtstamp,tframe[1])
        if tframe!=end_truncate:
            mintstamp = min(mintstamp,tframe[0])
        new_box = tfbox.TimeFreqBox((mintstamp,maxtstamp),(minfreq,maxfreq),'lte')
        new_box.params['power'] = maxpwr
        new_tfreq_boxes.append(new_box)
        tfreq_boxes = [b for b in tfreq_boxes if b.time_intersection(tframe)==None]
    return new_tfreq_boxes

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
        self.fft_size = GrLTETracesFlowgraph.prb_mapping[self.n_prbs]
        self.samp_rate = float(self.fft_size*self.subcarrier_spacing)
        frames_path = os.path.expanduser('~/tmp/lte_frames')
        n_prbs_str = "%02d" % (self.n_prbs,)
        mcs_str = "%02d" % (self.mcs)
        fname = '{}/lte_dump_prb_{}_mcs_{}.32fc'.format(frames_path,n_prbs_str,mcs_str)
        self.expected_bw = GrLTETracesFlowgraph.fftsize_mapping[self.fft_size]
        self.resamp_ratio = 20.0e6/self.samp_rate
        self.n_samples_per_frame = int(10.0e-3*self.samp_rate)
        if isinstance(n_offset_samples,tuple):
            if n_offset_samples[0]=='uniform':
                self.n_offset_samples = np.random.randint(*n_offset_samples[1])
            else:
                raise NotImplementedError('I don\'t recognize this.')
        else:
            self.n_offset_samples = int(n_offset_samples)
        randgen = lf.random_generator.load_param(pad_interval)
        # scale by sampling rate
        new_params = [int(v/self.resamp_ratio) for v in randgen.params]
        randgen = lf.random_generator.load_generator(pad_interval)
        if isinstance(frequency_offset,tuple):
            assert frequency_offset[0]=='uniform'
            self.frequency_offset = frequency_offset[1]
        else: # it is just a value
            self.frequency_offset = [frequency_offset]

        # blocks
        self.file_reader = blocks.file_source(gr.sizeof_gr_complex,fname,True)
        self.tagger = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex,1,self.n_samples_per_frame,"packet_len")
        self.burst_shaper = specmonitor.random_burst_shaper_cc(randgen.dynrandom(), 0, self.frequency_offset,"packet_len")
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
    # print_params(d,__name__)

    while True:
        # create general_mod block
        tb = GrLTETracesFlowgraph.load_flowgraph(d)

        logger.info('Starting GR waveform generator script for LTE')
        tb.run()
        logger.info('GR script finished')

        gen_data = np.array(tb.dst.data())

        try:
            v = wav_utils.transform_IQ_to_sig_data(gen_data,args)

            # merge boxes if broadcast channel is empty
            metadata = v.get_stage_derived_params('spectrogram_img')
            # metadata = sda.get_stage_derived_parameter(v, 'spectrogram_img_metadata', args['stage_name'])
            tfreq_boxes = copy.deepcopy(metadata.tfreq_boxes)
            new_tfreq_boxes = merge_boxes_within_same_lte_frame(gen_data,
                tfreq_boxes,tb.fft_size)
            metadata.tfreq_boxes = new_tfreq_boxes
            # NOTE: being a Ptr, it should be stored in the multi_stage_data
            # sda.set_stage_derived_parameter(v, args['stage_name'], 'spectrogram_img_metadata', metadata)
        except RuntimeError, e:
            logger.warning('Going to re-run radio')
            continue
        break

    # save file
    v.save_pkl()

class LTEDLGenerator(lf.SignalGenerator):
    @staticmethod
    def run(args):
        run(args)
    @staticmethod
    def name():
        return 'lte_dl'
