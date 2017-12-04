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

from ..sig_format import sig_data_access as sda
from ..data_representation import image_representation as imgrep
from ..data_representation import timefreq_box as tfbox
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def print_params(params,name):
    logger.debug('%s waveform generator starting',name)
    for k, v in params.iteritems():
        logger.debug('%s: %s (type=%s)', k, v, type(v))

def create_new_sigdata(args):
    logger.debug('Going to fill the stage data structure')
    # generate a sig object/dict
    v = sda.init_metadata()

    # add the stage parameters that were passed to the waveform generator
    sda.set_stage_parameters(v, args['stage_name'], args['parameters'])

    return v

def set_derived_sigdata(stage_data,x,args):
    sig2img_params = args['parameters']['signal_representation']
    signalimgmetadata = imgrep.get_signal_to_img_converter(sig2img_params)
    box_label = args['parameters'][sig2img_params['boxlabel']]

    section_bounds = [0,x.size]
    sigmetadata = signalimgmetadata.generate_metadata(x,section_bounds,sig2img_params,box_label)
    
    # normalize boxes power
    tfreq_boxes = sigmetadata.tfreq_boxes
    tfreq_boxes,max_pwr = tfbox.normalize_boxes_pwr(tfreq_boxes,x)
    sigmetadata.tfreq_boxes = tfreq_boxes
    y = x/np.sqrt(max_pwr)

    # fill sigdata
    stage_data['IQsamples'] = y
    sda.set_stage_derived_parameter(stage_data, args['stage_name'], 'spectrogram_img_metadata', sigmetadata)

def transform_IQ_to_sig_data(x,args):
    """
    This function should return a dictionary/obj with: IQsamples,
    stage parameters that were passed, and the derived bounding_boxes
    """
    try:
        v = create_new_sigdata(args)
        set_derived_sigdata(v,x,args)
    except KeyError, e:
        logger.error('The input arguments do not seem valid. I received: {}'.format(args))
        raise
    return v
