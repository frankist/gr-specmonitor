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
import pickle
import copy

from ..sig_format import sig_data_access as sda
from ..sig_format import pkl_sig_format
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def time_average_Sxx_and_boxes(Sxx,tfreq_boxes,num_averages,step):
    # n_rows = int(np.floor((Sxx.shape[0]-(num_averages*overlap_ratio))/(num_averages*(1-overlap_ratio))))
    n_rows = int(np.floor((Sxx.shape[0]-(num_averages-step))/step))
    Syy = np.zeros((n_rows,Sxx.shape[1]))

    for r in range(Syy.shape[0]):
        Syy[r,:] = np.mean(Sxx[r*step:r*step+num_averages,:],axis=0)

    return Syy

def run(args):
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']
    params = args['parameters']
    num_averages = params['n_fft_averages']
    spec_avg_step = params.get('n_fft_step',num_averages)
    img_row_offset = params['img_row_offset']
    img_window = (img_row_offset,img_row_offset+params['img_n_rows'])

    ### get dependency file, and create a new stage_data object
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    section = freader.read_section()

    spec_metadata = sda.get_stage_derived_parameter(stage_data,'section_spectrogram_img_metadata')

    if len(spec_metadata)!=1:
        raise NotImplementedError('I assume that this file has one section. To be extended in the future') #TODO

    l = []
    for i in range(len(spec_metadata)):
        new_specdata = copy.deepcopy(spec_metadata[i])
        new_specdata.set_num_fft_averages(num_averages,spec_avg_step)
        new_specdata.slice_by_img_dims(img_window[0],img_window[1])
        l.append(new_specdata)
    sda.set_stage_derived_parameter(stage_data,args['stage_name'],'subsection_spectrogram_img_metadata',l)

    with open(targetfilename,'w') as f:
        pickle.dump(stage_data,f)
    logger.info('Finished writing resulting signal to file %s',targetfilename)
