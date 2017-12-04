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

def transform_IQ_to_sig_data(x,args):
    """
    This function should return a dictionary/obj with: IQsamples,
    stage parameters that were passed, and the derived bounding_boxes
    """
    v = create_new_sigdata(args)
    signalimg = imgrep.get_signal_to_img_converter(args['signal_representation'])
    # sigdata is going to be filled with boxes, their power and label
    signalimg.set_derived_sigdata(v,x,args)
    return v
