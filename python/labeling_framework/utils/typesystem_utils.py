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
from collections import Iterable
import numpy as np
import inspect
import copy
import cPickle as pickle
from ..labeling_tools.parametrization import random_generator
from . import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class ValueGenerator(object):
    def generate(self):
        pass

# NOTE: Test this properly. What happens to dictionaries?
def convert2list(v):
    if not isinstance(v,Iterable) or isinstance(v,basestring) or issubclass(v.__class__,ValueGenerator):
        return [v]
    elif not isinstance(v,list):
        return list(v)
    return v

def is_class_instance(obj):
    if not hasattr(obj, '__dict__'): # must have __dict__ to be a class
        return False
    if inspect.isroutine(obj): # cannot be a function/method
        return False
    if inspect.isclass(obj): # must be an instance
        return False
    else:
        return True

def np_to_native(v):
    ret = None
    if isinstance(v,np.generic): # it is np.float32, etc.
        ret = np.asscalar(v)
    elif isinstance(v,np.ndarray): # it is an np.array
        ret = v.tolist()
    elif is_class_instance(v): # it is a class object
        if issubclass(v.__class__,ValueGenerator): # create an instance
            ret = v.generate()
        else:
            if issubclass(v.__class__,random_generator):
                ret = copy.deepcopy(v)#pickle.loads(pickle.dumps(v))
            else:
                ret = copy.deepcopy(v)
                for member,val in vars(ret).items():
                    setattr(ret,member,np_to_native(val))
    elif not isinstance(v,Iterable) or isinstance(v,basestring): # it is POD type or string
        ret = v # it is already a native
    elif isinstance(v,list):
        ret = [np_to_native(e) for e in v]
    elif isinstance(v,tuple):
        ret = tuple([np_to_native(e) for e in v])
    elif isinstance(v,dict):
        ret = {np_to_native(k):np_to_native(e) for k,e in v.items()}
    else:
        err_msg = 'Please define a conversion for type '+type(v)
        logger.error(err_msg)
        raise NotImplementedError(err_msg)
    return ret

if __name__ == '__main__':
    pass
