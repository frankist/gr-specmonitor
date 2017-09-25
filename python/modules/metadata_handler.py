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

def convert2list(v):
    if not isinstance(v,Iterable) or type(v) is str:
        return [v]
    elif type(v) is tuple:
        return list(v)
    return v

class LabelParam:
    def __init__(self,label,value):
        if type(label) is not str:
            raise ValueError('ERROR: expected a string as parameter name. Got {}'.format(label))
        self.__val__ = (label,convert2list(value))
    def label(self):
        return self.__val__[0]
    def value(self):
        return self.__val__[1]
    def to_tuple(self): # for itertools flattening
        return ([self.__val__[0]],self.__val__[1])
    def to_dict(self): # for json conversion
        return {self.__val__[0]:self.__val__[1]}

def params_to_pickle(it,result_filename): # I use pickle instead of JSON to keep format at destiny
    # l = [param.to_dict() for param in it]
    d = {param.to_dict() for param in it}
    return pickle.dumps({'result_filename':result_filename,'parameters':d})

class ParamProduct:
    def __init__(self,param_list,true_predicates=None):
        self.param_names = tuple([p[0] for p in param_list])
        self.param_list = [p[1] for p in param_list]
        self.predicates = true_predicates

    def get_iterable(self):
        prod = itertools.product(*self.param_list)
        for p in self.predicates:
            prod = itertools.ifilter(p,prod)
        return prod

class ParamProductChain:
    def __init__(self,param_names,param_list):
        self.param_names = param_names
        self.param_list = param_list
        for p in self.param_list:# convert numbers or strings to lists
            for v in p:
                if (len(v)==1 and type(v) not in [list,tuple]) or type(v) is str:
                    raise ValueError('ERROR: Value {} has to be iterable and not string'.format(v))

    def get_iterable(self):
        return itertools.chain(*[itertools.product(*v) for v in self.paramlist])

    @classmethod
    def parse_list(cls,l):
        return cls(l[0],l[1])

class ParamProductJoin:
    def __init__(self,param_prod_list): # here not even the labels have to be the same
        self.param_prod_list = []
        for prod_list in param_prod_list:
            l = []
            for pair in prod_list:
                l.append(LabelParam(pair[0],pair[1]))
            self.param_prod_list.append(l)

    def get_iterable(self):
        prod = []
        for prod_list in self.param_prod_list:
            l = []
            for pair in prod_list:
                # print list(itertools.product(*pair.to_tuple()))
                l.append(itertools.product(*pair.to_tuple())) # we get ('label',value) pairs here
            prod.append(itertools.product(*l))
        return itertools.chain(*prod)

stage_names = ['waveform','Tx','RF','Rx']
format_extension = 'pkl'

class MultiStageParamHandler:
    def __init__(self,staged_params):
        self.staged_params = staged_params

    # def possible_stage_combinations(self,stage):
    #     p = self.staged_params[0:stage+1]
    #     params_flattened = itertools.chain(p)
    #     return params_flattened

    def stage_values(self,stage):
        return [a for a in self.staged_params[stage].param_list]

    def stage_iterable(self,stage,idx_range=None):
        v = self.staged_params[stage].get_iterable()
        if idx_range is None:
            return v
        if len(idx_range)>1:
            return itertools.islice(v,*idx_range)
        return itertools.islice(v,idx_range)

class FilenameUtils:
    def __init__(self):
        pass

    @staticmethod
    def get_stage_format(stage_number):
        fmt_str = '{}/data'.format(stage_names[stage_number])
        fmt_str += '_{}'*stage_number
        fmt_str += '.{}' % (format_extension)
        return fmt_str

    @staticmethod
    def get_stage_filename(stage_number,stage_run_idxs):
        fmt_str = FilenameUtils.get_stage_format(stage_number)
        fmt_str.format(*stage_run_idxs)
        return fmt_str

    @staticmethod
    def get_stage_filename_list(stage_sizes):
        stage_number = len(stage_sizes)
        fmt_str = FilenameUtils.get_stage_format(stage_number)
        prod_file_idxs = itertools.product(*[range(a) for a in stage_sizes])
        return [fmt_str.format(*v) for v in prod_file_idxs]

    @staticmethod
    def parse_filename():
        pass

def load_handler(filename):
    p = pickle.load(filename)

########### TESTING #############

def test_product_and_chain():
    pchain = ParamProductChain(
        ('type','fileno'),
        [(['lte'],range(5)),
         (['wifi'],range(3))
        ])
    pprod = ParamProduct([
        ('type',['lte','wifi']),
        ('fileno',range(5))
    ],[lambda x : not (x[0]=='wifi' and x[1]>=3)])
    # print pprod.param_list
    l = list(pchain.get_iterable())
    l2 = list(pprod.get_iterable())
    assert l == l2
    assert l[0]==('lte',0)
    # print l

def test_product_join():
    pprod1 = [
        ('type',['wifi']),
        ('encoding',range(4))
    ]
    pprod2 = [
        ('type',['lte']),
        ('bw',range(3))
    ]
    prodjoin = ParamProductJoin([pprod1,pprod2])
    l = list(prodjoin.get_iterable())
    print l

def test_staged_params():
    waveform_list = ['PC','LFM','PM']
    freq_list = np.append(np.linspace(-0.5,0.5,100),np.nan)
    pprod = ParamProduct([
        ('type',waveform_list),
        ('freq_excursion',freq_list)
    ], [lambda x : (bool(x[0]=='LFM') ^ bool(np.isnan(x[1])))])

    meta_handler = MultiStageParamHandler([pprod])
    v = meta_handler.stage_values(0)
    assert v[0] == waveform_list
    np.testing.assert_array_equal(v[1],freq_list)

    itrange = meta_handler.stage_iterable(0)
    l = list(itrange)
    assert(len(l)==(len(freq_list)-1+2))

    itrange = meta_handler.stage_iterable(0,(0,4))
    l = list(itrange)
    assert(len(l)==4)
    assert l[0][0] == waveform_list[0]
    assert l[1] == (waveform_list[1],freq_list[0])

if __name__ == '__main__':
    test_product_join()
    # test_product_and_chain()
    # test_staged_params()
