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
from ..labeling_tools import bounding_box as bb
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)


def print_params(params,name):
    logger.debug('%s waveform generator starting',name)
    for k, v in params.iteritems():
        logger.debug('%s: %s (type=%s)', k, v, type(v))

def create_waveform_sig_data(IQsamples,args,box_list,box_pwr_list):
    """
    This function should return a dictionary/obj with: IQsamples,
    stage parameters that were passed, and the derived bounding_boxes
    """
    logger.debug('Going to fill the stage data structure')
    # generate a sig object/dict
    v = sda.init_metadata()

    # fill with samples
    v['IQsamples'] = IQsamples

    # add the stage parameters that were passed to the waveform generator
    sda.set_stage_parameters(v, args['stage_name'], args['parameters'])

    # add the parameters that were derived
    sda.set_stage_derived_parameter(v, args['stage_name'], 'bounding_boxes',
                                    box_list)
    sda.set_stage_derived_parameter(v, args['stage_name'], 'bounding_boxes_power',
                                    box_pwr_list)

    return v

def derive_bounding_boxes(x):
    logger.debug('Going to compute Bounding Boxes')
    box_list = bb.compute_bounding_boxes(x)
    logger.debug('Finished computing the Bounding Boxes')

    # normalize the power of the signal
    box_pwr_list = bb.compute_boxes_pwr(x, box_list)
    max_pwr_box = np.max(box_pwr_list)
    y = x/np.sqrt(max_pwr_box)

    #debug
    # plt.plot(np.abs(gen_data))
    # plt.plot(np.abs(gen_data0),'r')
    # plt.show()
    return (y,box_pwr_list,box_list)

def transform_IQ_to_sig_data(x,args):
    y,box_pwr_list,box_list = derive_bounding_boxes(x)
    v = create_waveform_sig_data(y,args,box_list,box_pwr_list)
    return v

if __name__ == '__main__':
    pass
