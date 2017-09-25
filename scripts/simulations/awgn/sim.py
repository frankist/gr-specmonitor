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
sys.path.append('../../../python/modules')
import metadata_handler as mh

stage_names = ['waveform','Tx','RF','Rx']

# waveform_params = mh.ParamProductChain(
#     ('type','encoding'), # parameter names
#     [('LTE',range(100)), # parameter list of products
#      ('WLAN',range(8),),
#      ('DC',1)
#     ]
#     # ('freq_excursion',np.linspace(-0.5,-0.5,100))
# )
# Tx_param_values = (
#     ('time_offset','phase_offset','window_offset','soft_gain','frequency_offset'),
#     [(range(0,1000,5),np.linspace(-np.pi,np.pi,100),[1000],np.linspace(0.01,1,100),np.linspace(-0.45,0.45,100))]
# )
LTE_params = [
    ('waveform','LTE'),
    ('BW',[1.4,5,10,20])
]
WIFI_params = [
    ('waveform','WIFI'),
    ('BW',[1.4,5,10,20])
]
waveform_params = ParamProductJoin([LTE_params,WIFI_params])
Tx_params = mh.ParamProductJoin([
    ('time_offset',range(0,1000,5)),
    ('phase_offset',np.linspace(-np.pi,np.pi,100)),
    ('window_size',1000),
    ('n_windows',10),
    ('soft_gain',np.linspace(0.01,1,100)),
    ('frequency_offset',np.linspace(-0.45,0.45,100))
])
RF_params = mh.ParamProductJoin([
    ('awgn',1),
    ('hard_gain',1),
    ('centre_frequency',2.3e9)
])
Rx_params = mh.ParamProductJoin([
    ('rx_mult_coef',1)
])

# TODO: GENERATE waveform_params from files that exist in the "waveform_templates" folder
# and create "waveform" folder with files numbered and all tidied up

def generate_params():
    # TODO:waveform_params = read_folder('waveform_templates')
    param_handler = MultiStageParamHandler([waveform_params,Tx_params, RF_params, Rx_params])
    # TODO:save param_handler for later loading

def generate_fileformat(lvl):
    format_str = 'data'
    for i in range(lvl):
        format_str += '_{}'
    format_str+='pkl'

class MakeFileSimulator:
    def __init__(self):#TODO
        self.__multistage_handler__ = None

    def get_multistage_handler(self):#TODO
        pass

    def generate_filenames(self,level_list):
        def generate_stage_filenames(lvl):
            handler = self.get_multistage_handler()
            stage_sizes = [handler.get_stage_size(a) for a in range(lvl)]
            return FilenameUtils.get_stage_filename_list(stage_sizes)
        if type(level_list) in [list,tuple]:
            return [generate_stage_filenames(v) for v in level_list]
        return [generate_stage_filenames(level_list)]

    def print_filenames(self,level_list):
        fnames = self.generate_filenames(level_list)
        for f_list in fnames:
            for f in f_list:
                print f

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
