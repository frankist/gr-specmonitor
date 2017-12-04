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

############ data transformation helpers ##############

def normalize_image_data(img_data):
    val_range = (np.min(img_data),np.max(img_data))
    data_norm = (img_data-val_range[0])/(val_range[1]-val_range[0])
    assert np.max(data_norm)<=1.0 and np.min(data_norm)>=0
    return data_norm

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

def register_image_representation(name,signal_img_child):
    __format_types__[name] = signal_img_child

def get_signal_to_img_converter(params):
    assert isinstance(params,dict)
    format_name = params['format_type']

    # this adds to the known img formats the one we need
    filename = format_name+'.py'
    importlib.import_module(filename)

    # delegate
    return known_img_formats[format_name]
