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
import sys
import os

class arg_params:
    def __init__(self,name,shortname,values):
        self.name = name
        self.shortname = shortname
        self.values = values

params = []
params.append(arg_params('waveform','w',range(10)))
params.append(arg_params('SNRdB','snr',range(-5,20)))
params.append(arg_params('RUN','r',range(10)))

def generate_fileformat():
    s = 'results/sim'
    for i in range(len(params)):
        s=s+'_'+params[i].shortname+'_{}'
    s=s+'.pkl'
    return s

def parse_filename(f):
    fbase = os.path.splitext(os.path.basename(f))[0]
    tokens = fbase.split('_')
    return (tokens[2],tokens[4],tokens[6])

###############
### Options ###
###############

def generate_filenames():
    fileformat = generate_fileformat()
    l = [fileformat.format(*x)+'\n' for x in itertools.product(*[params[i].values for i in range(len(params))])]
    print ''.join(l)

def print_filename():
    f = sys.argv[2]
    print 'Going to generate file: ', f
    x = parse_filename(f)
    l=''
    for i in range(len(x)):
        l=l+params[i].name+' = '+ x[i] +'\n'
    print l

def command_args():
    f = sys.argv[2]
    x = parse_filename(f)
    l = ''
    for i in range(len(x)):
        l=l+'--{}={} '.format(params[i].name,x[i])
    print l

#######################
### Parse the input ###
#######################

if len(sys.argv)<=1:
    raise NotImplementedError("Need to provide more arguments")
possibles = globals().copy()
possibles.update(locals())
method = possibles.get(sys.argv[1])
if not method:
     raise NotImplementedError("Method %s not implemented" % sys.argv[1])
method()
