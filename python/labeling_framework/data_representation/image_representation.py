#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2017
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
import importlib
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

############ data transformation helpers ##############

def normalize_image_data(img_data,strict_bounds=False):
    val_range = (np.min(img_data),np.max(img_data))
    data_norm = (img_data-val_range[0])/(val_range[1]-val_range[0])
    if not (np.max(data_norm)<=1.0 and np.min(data_norm)>=0):
        if strict_bounds is False and val_range[0]==-np.inf:
            # if not strict, recompute normalized image
            minval = np.min(np.isfinite(img_data))
            idxs = np.isneginf(img_data)
            img2 = np.array(img_data)
            img2[idxs] = minval
            data_norm = normalize_image_data(img2)
            logger.warning('Normalization Failed. This was the img limits: {}. I am gonna set a minimum value of {}'.format(val_range,minval))
        else:
            raise RuntimeError('Normalization Failed. This was the img limits: {}'.format(val_range))
    return data_norm

# consider deleting
class SignalImgConverter(object):
    @staticmethod
    def set_derived_sigdata(stage_data,x,args):
        raise NotImplementedError('This is an abstract class')

    @staticmethod
    def image_data(x,representation_params):
        raise NotImplementedError('This is an abstract class')

    @staticmethod
    def generate_bounding_boxes(stage_data,stage_name):
        raise NotImplementedError('This is an abstract class')

########## register your img generators #############

__format_types__ = {}

def register_signal_to_img_converter(name,signal_img_child):
    __format_types__[name] = signal_img_child

def get_signal_to_img_converter(params):
    assert isinstance(params,dict)
    format_name = params['format_type']

    if format_name not in __format_types__:
        logger.info('Going to import the input representation {}'.format(format_name))
        # this adds to the known img formats the one we need
        filename = 'labeling_framework.data_representation.'+format_name#+'.py'
        importlib.import_module(filename)

    # delegate
    return __format_types__[format_name]

def signal_to_img_converter_factory(params): # NOTE: consider deleting the get_signal_to_img_converter
    return get_signal_to_img_converter(params)

# class SignalRepresentation(object):
#     def __init__(self,sig2imgparams,IQsamples):
#         pass

#     def generate_metadata(self):
#         raise NotImplementedError('This method needs to be implemented')

#     def generate_representation(self):
#         raise NotImplementedError('This method needs to be implemented')

#     def representation_dims(self):
#         raise NotImplementedError('This method needs to be implemented')

#     def apply_transformation(self,**kwargs):
#         """
#         This method creates a new representation with both
#         IQsamples and metadata altered """
#         raise NotImplementedError('This method needs to be implemented')
