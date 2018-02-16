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
import copy

from ..data_representation import image_representation as imgrep
from ..data_representation import timefreq_box as tfbox
from ..core import SignalDataFormat as ssa
from ..labeling_tools.parametrization import random_generator
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

def print_params(params,name):
    logger.debug('%s waveform generator starting',name)
    for k, v in params.iteritems():
        logger.debug('%s: %s (type=%s)', k, v, type(v))

def set_derived_sigdata(x,args,fail_at_noTx):
    sig2img_params = args['parameters']['signal_representation']
    signalimgmetadata = imgrep.signal_to_img_converter_factory(sig2img_params)

    box_label = args['parameters'][sig2img_params['boxlabel']]

    section_bounds = [0,x.size]
    sigmetadata = signalimgmetadata.generate_metadata(x,section_bounds,sig2img_params,box_label)

    # assert there is at least one box
    if len(sigmetadata.tfreq_boxes)==0 and fail_at_noTx:
        raise RuntimeError('There were no Transmissions')

    # scale the signal and boxes power
    # frame_mag2_gen = random_generator.load_param(args['parameters'].get('frame_mag2',1))
    # y,tboxes = apply_normalization_and_random_scaling(x,sigmetadata.tfreq_boxes,frame_mag2_gen)
    # sigmetadata.tfreq_boxes = tboxes

    # # normalize boxes power
    # tfreq_boxes = sigmetadata.tfreq_boxes
    # tfreq_boxes,max_pwr = tfbox.normalize_boxes_pwr(tfreq_boxes,x)
    # sigmetadata.tfreq_boxes = tfreq_boxes
    # y = x/np.sqrt(max_pwr)

    return ssa.StageSignalData(args,{'spectrogram_img':sigmetadata},x)

def transform_IQ_to_sig_data(x,args,fail_at_noTx=True):
    """
    This function should return a dictionary/obj with: IQsamples,
    stage parameters that were passed, and the derived bounding_boxes
    """
    try:
        # v = create_new_sigdata(args)
        this_stage_data = set_derived_sigdata(x,args,fail_at_noTx)
        v2 = ssa.MultiStageSignalData()
        v2.set_stage_data(this_stage_data)
    except KeyError, e:
        logger.error('The input arguments do not seem valid. I received: {}'.format(args))
        raise
    except RuntimeError, e:
        logger.warning('There were no transmissions during the specified window')
        raise e
    return v2

def aggregate_independent_waveforms(multi_stage_data_list):
    assert len(multi_stage_data_list)>=1
    combined_data = copy.deepcopy(multi_stage_data_list[0])
    for i in range(1,len(multi_stage_data_list)):
        combined_data = ssa.combine_multi_stage_data(combined_data,multi_stage_data_list[i])
    return combined_data

def random_scale_mag2(tboxes,randgen):
    scale_values = randgen.generate(len(tboxes))
    if isinstance(scale_values,float):
        scale_values = [scale_values]
    for i in range(len(tboxes)):
        tboxes[i].params['power'] *= scale_values[i]
    return tboxes

def normalize_mag2(tboxes):
    pwr_list = [b.params['power'] for b in tboxes]
    max_mag2 = np.max(pwr_list)
    for i in range(len(tboxes)):
        tboxes[i].params['power'] /= max_mag2
    return tboxes

def set_signal_mag2(x,tboxes):
    y = np.array(x)
    x_mag2_list = np.array(tfbox.compute_boxes_pwr(x,tboxes))
    for i in range(len(tboxes)):
        y[tboxes[i].time_bounds[0]:tboxes[i].time_bounds[1]] *= np.sqrt(tboxes[i].params['power']/x_mag2_list[i])
    return y

