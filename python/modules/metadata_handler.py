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
import itertools
from collections import Iterable
import importlib
import os
import pickle
from filename_utils import *
import typesystem_utils as ts
import collections
import session_params

def params_to_pickle(it,result_filename): # I use pickle instead of JSON to keep format at destiny
    # l = [param.to_dict() for param in it]
    d = {param.to_dict() for param in it}
    return pickle.dumps({'result_filename':result_filename,'parameters':d})

# class ParamProduct:
#     def __init__(self,param_list,true_predicates=None):
#         self.param_names = tuple([p[0] for p in param_list])
#         self.param_list = [p[1] for p in param_list]
#         self.predicates = true_predicates

#     def get_iterable(self):
#         prod = itertools.product(*self.param_list)
#         for p in self.predicates:
#             prod = itertools.ifilter(p,prod)
#         return prod

# class ParamProductChain:
#     def __init__(self,param_names,param_list):
#         self.param_names = param_names
#         self.param_list = param_list
#         for p in self.param_list:# convert numbers or strings to lists
#             for v in p:
#                 if (len(v)==1 and type(v) not in [list,tuple]) or type(v) is str:
#                     raise ValueError('ERROR: Value {} has to be iterable and not string'.format(v))

#     def get_iterable(self):
#         return itertools.chain(*[itertools.product(*v) for v in self.paramlist])

#     @classmethod
#     def parse_list(cls,l):
#         return cls(l[0],l[1])

# class MultiStageParameters:
#     def __init__(self,params,stage_order,tag_order):
#         self.stage_names = stage_order
#         self.tag_names = tag_order
#         # make param_values an ordered Dict
#         self.param_values = collections.OrderedDict(sorted(self.params.items(),key=lambda x: self.tag_names.index(x[0])))
#         for k in self.tag_names:
#             self.param_values[k] = collections.OrderedDict(sorted(self.param_values[k].items(),
#                                                                   key=lambda x: self.stage_names.index(x[0])))

#     def get_iterable(self):
#         prod = []
#         for tag,tag_values in self.param_values:
#             for stage_name,stage_params in tag_values:
#                 l = [('tag',tag)]
#                 for pair in stage_params:
#                     l.append(itertools.product(*pair.to_tuple()))
#                 prod.append()


# class ParamProductJoin:
#     def __init__(self,param_prod_list): # here not even the labels have to be the same
#         self.product_size = 0
#         self.param_prod_list = []
#         for prod_list in param_prod_list:
#             l = [LabeledParamValues(pair[0],pair[1]) for pair in prod_list]
#             self.product_size += np.cumprod([v.number_values() for v in l])[-1]
#             self.param_prod_list.append(l)

#     def get_iterable(self):
#         prod = []
#         for prod_list in self.param_prod_list:
#             l = []
#             for pair in prod_list:
#                 # print list(itertools.product(*pair.to_tuple()))
#                 l.append(itertools.product(*pair.to_tuple())) # we get ('label',value) pairs here
#             prod.append(itertools.product(*l))
#         return itertools.chain(*prod)

#     def get_size(self):
#         return self.product_size

# class MultiStageParamHandler:
#     def __init__(self,staged_params):
#         self.staged_params = staged_params

#     def stage_values(self,stage):
#         return [a for a in self.staged_params[stage].param_list]

#     def stage_iterable(self,stage,idx_range=None):
#         v = self.staged_params[stage].get_iterable()
#         if idx_range is None:
#             return v
#         if type(idx_range) in [list,tuple]:#len(idx_range)>1:
#             return itertools.islice(v,*idx_range)
#         return itertools.islice(v,idx_range,idx_range+1)

#     def get_stage_size(self,stage):
#         return self.staged_params[stage].get_size()

class SessionParamsHandler:
    def __init__(self,stage_params,filenames_handler):
        self.filename_handler = filenames_handler
        self.stage_params = stage_params

    def session_name(self):
        return self.filename_handler.session_name

    def stage_name_list(self):
        return self.filename_handler.stage_name_list

    def save(self,fname):
        with open(fname,'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_cfg_file(cls,session_file,session_name,cfg_file):
        fbase = os.path.splitext(os.path.basename(cfg_file))[0]
        try:
            cfg_module = importlib.import_module(fbase)
        except Exception, e:
            print 'Error while opening config file: ',str(e)
            exit()
        # TODO: Parse the module to see if every variable is initialized
        sp = session_params.TaggedMultiStageParams(cfg_module.tags,cfg_module.stage_names,
                                                   cfg_module.stage_params)
        # MultiStageParamHandler(cfg_module.stage_params)
        sfh = SessionFilenamesHandler(session_file,session_name,cfg_module.stage_names)
        session_handler = cls(sp,sfh)
        return session_handler

    @staticmethod
    def load_handler(session_file):
        with open(session_file,'r') as f:
            return pickle.load(f)

########### TESTING #############

def test_fileutils():
    l = FilenameUtils.get_stage_filename_list([5,4,3])
    print l

# def test_product_join():
#     pprod1 = [
#         ('type',['wifi']),
#         ('encoding',range(4))
#     ]
#     pprod2 = [
#         ('type',['lte']),
#         ('bw',range(3))
#     ]
#     prodjoin = ParamProductJoin([pprod1,pprod2])
#     l = list(prodjoin.get_iterable())
#     print l

# def test_staged_params():
#     waveform_list = ['PC','LFM','PM']
#     freq_list = np.append(np.linspace(-0.5,0.5,100),np.nan)
#     pprod = ParamProduct([
#         ('type',waveform_list),
#         ('freq_excursion',freq_list)
#     ], [lambda x : (bool(x[0]=='LFM') ^ bool(np.isnan(x[1])))])

#     meta_handler = MultiStageParamHandler([pprod])
#     v = meta_handler.stage_values(0)
#     assert v[0] == waveform_list
#     np.testing.assert_array_equal(v[1],freq_list)

#     itrange = meta_handler.stage_iterable(0)
#     l = list(itrange)
#     assert(len(l)==(len(freq_list)-1+2))

#     itrange = meta_handler.stage_iterable(0,(0,4))
#     l = list(itrange)
#     assert(len(l)==4)
#     assert l[0][0] == waveform_list[0]
#     assert l[1] == (waveform_list[1],freq_list[0])

if __name__ == '__main__':
    test_fileutils()
    # test_product_join()
    # test_product_and_chain()
    # test_staged_params()
