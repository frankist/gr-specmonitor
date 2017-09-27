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
# import digital_rf as drf
from json import JSONDecoder
from functools import partial

# I need to polymorph this bc I may have multiple signal formats

# def json_parse(fileobj, key_halt='IQsamples', buffersize=2048, decoder=JSONDecoder()):
#     buffer = ''
#     for chunk in iter(partial(fileobj.read, buffersize), ''):
#          buffer += chunk
#          while buffer:
#              try:
#                  result_tmp, index = decoder.raw_decode(buffer)
#                  if key_halt in result.keys():
#                      del result['key_halt']
#                      return result
#                  buffer = buffer[index:]
#              except ValueError:
#                  # Not enough data to decode, read more
#                  break

class WaveformFileReader:
    def __init__(self):
        pass

    @abstractmethod
    def size(self):
        pass

    @abstractmethod
    def metadata(self):
        pass

    @abstractmethod
    def read_section(self, start, end):
        pass

class WaveformPklReader(WaveformFileReader):
    def __init__(self,fname):
        self.wavdata = pickle.load(fname)

    def size():
        return self.wavedata['IQsamples'].size

    def metadata():
        return self.wavedata['metadata']

    def read_section(self,idx=0,end_idx=None):
        if end_idx is None:
            return self.wavdata['IQsamples'][idx::]
        else:
            return self.wavdata['IQsamples'][idx:end_idx]

def write_waveform_pickle(fname,IQsamples,metadata):
    d = {'IQsamples':IQsamples,'metadata':metadata}
    pickle.dump(fname,d)

# class BoundingBoxSignal:
#     def __init__(self, tstart,tend,frac_bw):
#         self.tstart = tstart
#         self.tend = tend
#         self.frac_bw = frac_bw

#     def to_dict(self):
#         return {'start':self.tstart,'end':self.tend,'fractional_bw':self.frac_bw}

#     @staticmethod
#     def from_dict(d):
#         return BoundingBoxSignal(d['start'],d['end'],d['fractional_bw'])
