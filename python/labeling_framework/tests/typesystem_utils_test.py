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
import sys

# load labeling_framework package
sys.path.append('../../')

# load file to test
from labeling_framework.utils import typesystem_utils as ts

class randomclass:
    def __init__(self):
        self.m1 = 1.0
        self.m2 = 'ola'

if __name__ == '__main__':
    d = {'waveform':
         {
             'param1':'value1',
             'param2':[1,2.0],
             'param3':('string_type',2.0),
             'param4':randomclass()
         },
         'Tx':
         [
             ('value',np.ones(5)),
             {
                 'lvl1':np.mean(np.ones(10)),
                 'lvl2':[np.max(np.ones(5)),np.mean(np.zeros(5))]
             },
             ('complex',np.ones(5,dtype=np.complex64))
         ]
    }
    print 'result:',ts.np_to_native(d)
