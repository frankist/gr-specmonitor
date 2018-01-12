#!/usr/bin/env python

import numpy as np
import sys
sys.path.append('../../../python/')
from labeling_framework.utils import typesystem_utils

# NOTE: python generators are not pickeable :(
class SuperPoissonGenerator(typesystem_utils.ValueGenerator):
    def __init__(self,mean,offset=0,upbound=np.inf):
        self.mean = mean
        self.offset = offset
        self.upbound = upbound

    def generate(self):
        return min(self.offset+np.random.poisson(self.mean),self.upbound)

# def super_poisson(mean,offset,upbound=np.inf):
#     return np.min(offset+np.random.poisson(mean),upbound)

# def generic_generator(func,*args):
#     while True:
#         yield func(*args)

num_sections = 1
section_size = 100000
toffset_range = [100]
frequency_offset = [-0.325,-0.125,0.125,0.325] #[-0.5,0.5]
skip_samps = 0
wf_gen_samps = section_size*num_sections + toffset_range[-1] + skip_samps + 50

tags = ['wifi','psk']
ssh_hosts = ['USRPRx']
stage_dependency_tree = {
    'Tx':'waveform',
    'RF':'Tx',
    'TxImg':'Tx',
    'Rx':'RF',
    'RFImg':'RF',
    'RFLabels':'RF',
    'RFVOCFormat':'Rx'
}

Tx_params = [
    ('frequency_offset',frequency_offset),
    ('time_offset',toffset_range),
    ('section_size',section_size),
    ('num_sections',num_sections),
    ('soft_gain',[1.0]),
    ('noise_voltage',[0])
]
Tx_params_wifi = list(Tx_params)
for i,e in enumerate(Tx_params_wifi):
    if e[0]=='frequency_offset':
        Tx_params_wifi[i] = ('frequency_offset',0)

RF_params = [
    ('tx_gain_norm', 0.99),#10.0**np.arange(-20,0,5)),#range(0, 21, 10)),  #range(0,30,15)),
    ('settle_time', 0.25),
    ('rx_gaindB', 10.0),#range(0, 21, 10)),
    ('rf_frequency', 2.35e9)
]

Rx_params = [
    ('n_fft_averages',10),
    ('img_row_offset',[0,50]),
    ('img_n_rows',104),
]

RFVOCFormat_params = [
    ('img_size',[(104,104)])
]

spectrogram_representation = {'format_type':'spectrogram','boxlabel':'waveform',
                              'fftsize':64,'cancel_DC_offset':True}

stage_params = {
    'wifi':
    {
        'waveform':
        [
            ('waveform',['wifi']),
            ('number_samples',wf_gen_samps),
            ('sample_rate',20e6),
            ('encoding',[0]),
            ('pdu_length',[500]),
            ('pad_interval',5000),
            ('signal_representation',[spectrogram_representation])
        ],
        'Tx': Tx_params_wifi,
        'RF': RF_params,
        'Rx': Rx_params,
        'RFVOCFormat': RFVOCFormat_params
    },
    'sig':
    {
        'waveform':
        [
            ('waveform',['square','saw']),
            ('sample_rate',20e6),
            ('frequency',[1e4,5e5]),
            ('number_samples',wf_gen_samps),
            ('signal_representation',[spectrogram_representation])
        ],
        'Tx': Tx_params,
        'RF': RF_params,
        'Rx': Rx_params,
        'RFVOCFormat': RFVOCFormat_params
    },
    'psk':
    {
        'waveform':
        [
            ('waveform',['generic_mod']),
            ('sample_rate',20e6),
            ('number_samples',wf_gen_samps),
            ('constellation',['psk']),
            ('order',[2]),
            ('mod_code','GRAY'),
            ('differential',False),
            ('samples_per_symbol',10),
            ('excess_bw',0.25),
            ('pre_diff_code',False),
            ('burst_len', [('poisson',3000,1000)]),
            #SuperPoissonGenerator(3000,1000)),
            #generic_generator(super_poisson,3000,1000)),
            ('zero_pad_len',[('poisson',5000)]),
            #SuperPoissonGenerator(5000)),
            #generic_generator(np.random.poisson,5000)),#5000),
            ('signal_representation',[spectrogram_representation])
        ],
        'Tx': Tx_params,
        'RF': RF_params,
        'Rx': Rx_params,
        'RFVOCFormat': RFVOCFormat_params
    }
}
