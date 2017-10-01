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

import typesystem_utils as ts
import itertools
import numpy as np
import collections

# This object stores the label and possible values of a parameter
class LabeledParamValues:
    def __init__(self,label,value):
        if type(label) is not str:
            raise ValueError('ERROR: expected a string as parameter name. Got {}'.format(label))
        self.__val__ = (label,ts.convert2list(value))
    def label(self):
        return self.__val__[0]
    def values(self):
        return self.__val__[1]
    def to_tuple(self): # for itertools flattening
        return ([self.__val__[0]],self.__val__[1])
    def to_dict(self): # for json conversion
        return {self.__val__[0]:self.__val__[1]}
    def length(self):
        return len(self.values())
    def get_iterable(self):
        return itertools.product(*self.to_tuple())

# this is a list of (param,possible_values) pairs stored as "LabeledParamValues"
class StageParams:
    def __init__(self,param_list):
        self.labeled_params = [LabeledParamValues(pair[0],pair[1]) for pair in param_list]
        self.__product_size__ = np.cumprod([v.length() for v in self.labeled_params])[-1]

    def length(self):
        return self.__product_size__

    def get_iterable(self):
        prod_list = [pair.get_iterable() for pair in self.labeled_params]
        return itertools.product(*prod_list)

class MultiStageParams:
    def __init__(self,stage_names,stage_params):
        self.stage_names = stage_names
        # I keep the order of the stages according to the stage_names list
        self.stage_params = {k:StageParams(stage_params[k]) for k in self.stage_names}
        self.__stage_lengths__ = [self.stage_params[k].length() for k in self.stage_names]
        self.__param_length__ = np.cumprod([v.length() for v in self.stage_params.values()])[-1]

    def length(self,stage=None):
        if stage is None:
            return self.__param_length__
        else:
            stage_idx = stage if type(stage) is not str else self.stage_names.index(stage)
            return self.__stage_lengths__[stage_idx]

    def get_iterable(self,stage=None):
        if stage is not None:
            stage_key = stage if type(stage) is str else self.stage_names[stage]
            return self.stage_params[stage_key].get_iterable()
        else:
            return itertools.product(*[self.stage_params[s].get_iterable() for s in self.stage_names])

class TaggedMultiStageParams:
    def __init__(self,tag_order,stage_order,stage_params):
        def add_tag(untagged_params,tag):
            for stage_key in untagged_params.keys():
                untagged_params[stage_key].append(('session_tag',tag))
            return untagged_params
        self.tag_names = tag_order
        self.stage_names = stage_order
        self.multistage_params = {k:MultiStageParams(stage_order,add_tag(stage_params[k],k)) for k in self.tag_names}
        self.__stage_lengths__ = [np.sum([t.length(s) for t in self.multistage_params.values()]) for s in self.stage_names]
        self.__tag_lengths__ = [self.multistage_params[t].length() for t in self.tag_names]
        self.__param_length__ = np.sum([v.length() for v in self.multistage_params.values()])

    def length(self,tag=None,stage=None):
        if stage is None and tag is None:
            return self.__param_length__
        elif stage is None and tag is not None:
            tag_idx = tag if type(tag) is not str else self.tag_names.index(tag)
            return self.__tag_lengths__[tag_idx]
        elif stage is not None and tag is None:
            stage_idx = stage if type(stage) is not str else self.stage_names.index(stage)
            return self.__stage_lengths__[stage_idx]
        else:
            tag_key = tag if type(tag) is str else self.tag_names[tag]
            return self.multistage_params[tag_key].length(stage)

    def get_iterable(self,tag=None,stage=None):
        if tag is not None:
            tag_key = tag if type(tag) is str else self.tag_names[tag]
            # FIXME: Should I insert the tag in the iterable?
            return self.multistage_params[tag].get_iterable(stage)
        else:
            return itertools.chain(*[self.multistage_params[t].get_iterable(stage) for t in self.tag_names])

    def get_stage_iterable(self,stage,idx_range=None):
        v = self.get_iterable(stage=stage)
        if idx_range is None:
            return v
        if type(idx_range) in [list,tuple]:
            return itertools.islice(v,*idx_range)
        return itertools.islice(v,idx_range,idx_range+1)
