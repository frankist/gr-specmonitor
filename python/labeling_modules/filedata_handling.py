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

import preamble_utils
import random_sequence

# this is a couple of functions for interpreting the metadata. I put everything in this file
# so I have things consistent and not scattered across multiple files, and then if I want to make a change
# I do not have to make that change everywhere
# I want to avoid a class to force me not to add state

def init_metadata():
    data_dict = {}
    data_dict['parameters'] = {}
    data_dict['derived_parameters'] = {}
    return data_dict

def get_stage_parameter(data_dict,param_name,stage_name=None):
    d = data_dict['parameters']
    if stage_name is None: # searches everywhere
        for stage,params in d.items():
            if param_name in params:
                return params[param_name]
    else:
        if param_name in d[stage_name]:
            return d[stage_name][param_name]
    return None # didn't find it

def set_stage_parameters(data_dict,stage_name,stage_params):
    if stage_name not in data_dict['parameters']:
        data_dict['parameters'][stage_name] = {}
    # todo: assert stage_name is valid
    # todo: assert there are no repeated stage_param names
    data_dict['parameters'][stage_name] = stage_params

def set_stage_derived_parameter(data_dict,stage_name,param_name,param_val):
    if stage_name not in data_dict['derived_parameters']:
        data_dict['derived_parameters'][stage_name] = {}
    data_dict['derived_parameters'][stage_name][param_name] = param_val

def get_stage_derived_parameter(data_dict,param_name,stage_name=None):
    d = data_dict['derived_parameters']
    if stage_name is None: # searches everywhere
        for stage,params in d.items():
            if param_name in params:
                return params[param_name]
    else:
        if param_name in d[stage_name]:
            return d[stage_name][param_name]
    return None # didn't find it

def get_num_samples_with_framing(data_dict):
    return int(get_stage_parameter(data_dict,'num_sections')*get_stage_parameter(data_dict,'section_size'))

def get_preamble_params(data_dict):
    # TODO: Make this not hardcoded
    lvl2_diff_len = len(random_sequence.maximum_length_sequence(13*2))
    pseq_len = [13,61]
    pparams = preamble_utils.generate_preamble_type2(pseq_len,lvl2_diff_len)
    return pparams

def get_frame_params(data_dict):
    guard_len = 5
    awgn_guard_len = 100
    pparams = get_preamble_params(data_dict)
    section_size = get_stage_parameter(data_dict,'section_size')
    frame_dur = preamble_utils.frame_params.compute_frame_period(section_size,pparams.length(),guard_len,awgn_guard_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_guard_len,frame_dur)
    return fparams

def store_section_samples(data_dict,x,peaks):
    tstart = peaks[0].tidx
    num_samples = get_num_samples_with_framing(data_dict)
    y = x[tstart:tstart+num_samples] # this starts at the start of the preamble

def is_framed(data_dict):
    bounds = get_stage_derived_parameter(data_dict,'section_bounds')
    if bounds is None:
        return False
    return True

class SignalDataDocument:
    def __init__(self,doc = {}):
        self.doc = doc
        pass

    def get_stage_param(self,param_name,stage_name = None):
        d = self.doc['parameters']
        if stage_name is None: # searches everywhere
            for stage,params in d.items():
                if param_name in params:
                    return params[param_name]
        else:
            if param_name in d[stage_name]:
                return d[stage_name][param_name]
        return None # didn't find it

    def get_stage_deriv_param(self,param_name,stage_name = None):
        d = self.doc['derived_parameters']
        if stage_name is None: # searches everywhere
            for stage,params in d.items():
                if param_name in params:
                    return params[param_name]
        else:
            if param_name in d[stage_name]:
                return d[stage_name][param_name]
        return None # didn't find it

    def set_stage_params(self,stage_name,stage_params):
        if stage_name not in data_dict['parameters']:
            data_dict['parameters'][stage_name] = {}
        # todo: assert stage_name is valid
        # todo: assert there are no repeated stage_param names
        data_dict['parameters'][stage_name] = stage_params

    @classmethod
    def make_signal_document(cls):
        d = cls()
        d.doc['parameters'] = {}
        d.doc['derived_parameters'] = {}
        return d
