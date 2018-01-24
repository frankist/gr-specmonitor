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

import itertools
import numpy as np
import collections

from ..utils import typesystem_utils as ts
from ..utils.basic_utils import *

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
        self.__product_size__ = 1
        if len(self.labeled_params)!=0:
            self.__product_size__ = np.cumprod([v.length() for v in self.labeled_params])[-1]

    def length(self):
        return self.__product_size__

    def get_iterable(self):
        prod_list = [pair.get_iterable() for pair in self.labeled_params]
        return itertools.product(*prod_list)

class MultiStageParams:
    def __init__(self,stage_dep_tree,stage_params):
        self.stage_dep_tree = stage_dep_tree
        # I keep the order of the stages according to the stage_names list
        self.stage_params = {k:StageParams(stage_params.get(k,[])) for k in self.stage_names()}
        self.__stage_lengths__ = {k:self.stage_params[k].length() for k in self.stage_names()}
        self.__param_length__ = np.cumprod([v.length() for v in self.stage_params.values()])[-1]

    def stage_names(self):
        return self.stage_dep_tree.stage_names

    def length(self,stage=None):
        if stage is None:
            return self.__param_length__
        else:
            assert isinstance(stage,basestring)
            return self.__stage_lengths__[stage]
            # stage_idx = stage if type(stage) is not str else self.stage_names().index(stage)
            # return self.__stage_lengths__[stage_idx]

    def get_iterable(self,stage=None):
        if stage is not None:
            # stage_key = stage if type(stage) is str else self.stage_names()[stage]
            return self.stage_params[stage].get_iterable()
        else:
            return itertools.product(*[self.stage_params[s].get_iterable() for s in self.stage_names()])

class TaggedMultiStageParams:
    def __init__(self,tag_order,stage_dep_tree,stage_params):
        def add_tag(untagged_params,tag):
            for stage_key in untagged_params.keys():
                untagged_params[stage_key].append(('session_tag',tag))
            return untagged_params
        self.tag_names = tag_order
        self.stage_dep_tree = stage_dep_tree
        self.multistage_params = {k:MultiStageParams(self.stage_dep_tree,add_tag(stage_params[k],k)) for k in self.tag_names}
        self.__stage_lengths__ = {s:np.sum([t.length(s) for t in self.multistage_params.values()]) for s in self.stage_names()} # total lengths for each stage
        self.__tag_lengths__ = [self.multistage_params[t].length() for t in self.tag_names] # total lengths for each tag
        self.__param_length__ = np.sum([v.length() for v in self.multistage_params.values()]) # total length
        self.__length_matrix__ = np.zeros((len(self.tag_names),len(self.stage_names())),np.int32)
        for ti,t in enumerate(self.tag_names):
            for si,s in enumerate(self.stage_names()):
                self.__length_matrix__[ti,si] = self.multistage_params[t].length(s)

    def stage_names(self):
        return self.stage_dep_tree.stage_names

    def slice_stage_lengths(self,tags=[],stages=[]):
        tags = force_iterable_not_str(tags)
        stages = force_iterable_not_str(stages)
        tags = tags if len(tags)>0 else self.tag_names
        stages = stages if len(stages)>0 else self.stage_names()
        tidxs = np.array([self.tag_names.index(t) for t in tags],np.int32)
        sidxs = np.array([self.stage_names().index(t) for t in stages],np.int32)
        m = self.__length_matrix__ # stupid numpy doesn't slice matrices without affecting its dimensions
        m = m[tidxs,:].reshape(tidxs.size,m.shape[1])
        m = m[:,sidxs].reshape(m.shape[0],sidxs.size)
        return m

    def length(self,tags=[],stages=[]):
        m = self.slice_stage_lengths(tags,stages)
        return np.sum([np.cumprod(m[t,:])[-1] for t in range(m.shape[0])])

    def get_iterable(self,tags=[],stages=[]):
        tags = force_iterable_not_str(tags)
        tags = tags if len(tags)>0 else self.tag_names
        stages = force_iterable_not_str(stages)
        stages = stages if len(stages)>0 else self.stage_names()
        l = []
        for t in tags:
            for s in stages:
                l.append(self.multistage_params[t].get_iterable(s))
        return itertools.chain(*l)
    # def length(self,tag=None,stage=None):
    #     if stage is None and tag is None:
    #         return self.__param_length__
    #     elif stage is None and tag is not None:
    #         tag_idx = tag if type(tag) is not str else self.tag_names.index(tag)
    #         return self.__tag_lengths__[tag_idx]
    #     elif stage is not None and tag is None:
    #         # stage_idx = stage if type(stage) is not str else self.stage_names.index(stage)
    #         return self.__stage_lengths__[stage]
    #     else:
    #         tag_key = tag if type(tag) is str else self.tag_names[tag]
    #         return self.multistage_params[tag_key].length(stage)

    # def get_idx_tuples(self,stage):#,tag=None):
    #     dep_path = self.stage_dep_tree.stage_dep_path[stage] # finds path to root
    #     stage_dep_idxs = [self.stage_names().index(s) for s in dep_path]
    #     tag_idx_list = range(len(self.tag_names))#self.tag_names.index(tag) if tag is not None else range(len(self.tag_names))
    #     idx_tuple_per_tag_list = []
    #     first_lvl_cum = 0
    #     for t in tag_idx_list:
    #         len_per_stage = self.__length_matrix__[stage_dep_idxs,t]
    #         range_per_stage = [range(s) for s in len_per_stage]
    #         range_per_stage[0] = range(first_lvl_cum,first_lvl_cum+len_per_stage[0]) # for the first we start by where the tag left us
    #         first_lvl_cum += len_per_stage[0]
    #         idx_tuple_per_tag_list.append(itertools.product(*range_per_stage))
    #     return itertools.chain(*idx_tuple_per_tag_list)

        # if tag is not None:
        #     assert isinstance(tag,basestring)
        #     return self.multistage_params[tag].get_iterable(stage)
        # return itertools.chain(*[self.multistage_params[t].get_iterable(stage) for t in self.tag_names])

    # def get_stage_iterable(self,stage,tag=None,idx_range=None):
    #     """
    #     With this method I am allowed to pick a specific iterator through its index.
    #     """
    #     if idx_range is None:
    #         return self.get_iterable(stage=stage,tag=tag)
    #     # if stage==self.stage_dep_tree.root: # if we are at the root
    #     #     v = self.get_iterable(stage=stage)
    #     # else:
    #     assert tag is not None
    #     v = self.get_iterable(stage=stage,tag=tag) # you cannot find the iterator if you don't have the tag in case you are not at the root
    #     if isinstance(idx_range,(list,tuple,slice)): # we will make a slice
    #         return itertools.islice(v,*idx_range)
    #     return itertools.islice(v,idx_range,idx_range+1)

    # def get_tag_name(self,stage_idx_tuple):
    #     idx0 = stage_idx_tuple[0]
    #     root_name = self.stage_dep_tree.root
    #     v = self.get_stage_iterable(stage=root_name,idx_range=idx0)
    #     entry_params = dict(list(v)[0])
    #     return entry_params['session_tag']

    # def get_run_parameters(self,stage_name,stage_idx_tuple):
    #     this_stage_param_idx = stage_idx_tuple[-1]
    #     tag = self.get_tag_name(stage_idx_tuple)
    #     return dict(list(self.get_stage_iterable(stage=stage_name,tag=tag,idx_range=this_stage_param_idx))[0])

# utilities for stage idx tuple
# idx tuple format: (tag, stage0 idx, stage1 idx, ...)
# I don't create a class bc this has to be understood in the command line

def get_tag(stage_idx_tuple):
    return stage_idx_tuple[0]

def get_stage_idx(sessiondata,stage_idx_tuple,stage_name):
    dist2root = sessiondata.stage_dep_tree.distance_to_root(stage_name)
    return stage_idx_tuple[dist2root+1] # account for tag

# receives a iterator over the lsit of parameters, and slices it
def slice_param_iterator(stage_param_iterator,idx_range):
    if isinstance(idx_range,(list,tuple)):
        return itertools.islice(stage_param_iterator,*idx_range)
    elif isinstance(idx_range,slice):
        return itertools.islice(stage_param_iterator,idx_range)
    return itertools.islice(stage_param_iterator,idx_range,idx_range+1)

# NOTE: the stage_idx_tuple by itself cannot tell the stage name bc it is a tree of stages
def get_run_parameters(sessiondata,stage_idx_tuple,stage_name):
    tag = get_tag(stage_idx_tuple)
    this_stage_idx = get_stage_idx(sessiondata,stage_idx_tuple,stage_name)
    params = list(slice_param_iterator(sessiondata.get_iterable(tags=tag,stages=stage_name),this_stage_idx))
    d = dict(params[0])
    return ts.np_to_native(d)
    # return dict(list(sessiondata.get_stage_iterable(stage=stage_name,tag=tag,idx_range=this_stage_idx))[0])

def generate_session_run_idxs(sessiondata,final_stage):
    path2root = sessiondata.stage_dep_tree.path_to_root(final_stage) # [this stage, ..., root]
    path2root_idx = [sessiondata.stage_names().index(s) for s in path2root] # get the idxs

    l = []
    for t in sessiondata.tag_names:
        stage_len_list = sessiondata.slice_stage_lengths(stages=path2root,tags=t)
        assert stage_len_list.shape[0]==1 # should only have one tag
        stage_range_list = [range(si) for si in reversed(stage_len_list[0,:])] # [root,...,this stage]
        range_idx_tuple = [[t]]+stage_range_list
        l.append(itertools.product(*range_idx_tuple))
    return itertools.chain(*l)
