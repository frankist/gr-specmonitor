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

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import channels
import sys
import pickle
from bounding_box import *
import pkl_sig_format

('frequency_offset',np.linspace(-0.45,0.45,10)),
('time_offset',range(0,100,10))

def print_params(params):
    print 'sig_source_c starting'
    for k,v in params.iteritems():
        print k,v,type(v)

def compute_new_bounding_boxes(time_offset,section_size,freq_offset,box_list):
    w = BoundingBox((time_offset,time_offset+section_size),(-0.5,0.5))
    return [w.box_intersection(b).add(-time_offset,freq_offset) for b in box_list if w.box_insersection(b) is not None]

def apply_channel_model(args):
    params = args['parameters']
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']

    time_offset = params['time_offset']
    section_size = params['section_size']
    noise_voltage = params.get('noise_voltage',0)
    freq_offset = params.get('frequency_offset',0)
    epsilon = params.get('epsilon',1)
    taps = None
    seed = 0

    freader = WaveformPklReader(sourcefilename)
    if time_offset+section_size>=freader.number_samples():
        raise ValueError('The file is not large enough for the requested number of samples.')
    xsection = freader.read_section(time_offset,time_offset+section_size)

    tb = gr.top_block()

    source = blocks.vector_source_c(xsection, True)
    head = blocks.head(gr.sizeof_gr_complex,section_size)
    channel = channels.channel_model(noise_voltage,freq_offset)
    dst = blocks.vector_sink_c()

    tb.connect(source,head)
    tb.connect(head,channel)
    tb.connect(channel,dst)

    print 'STATUS: Starting GR waveform generator script'
    tb.run()
    print 'STATUS: GR script finished'

    gen_data = np.array(dst.data())

    v = {'parameters':args['parameters'],'IQsamples':gen_data}
    section_box = BoundingBox((time_offset,time_offset+section_size),(-0.5,0.5))
    box_list = compute_new_bounding_boxes(time_offset,section_size,freq_offset,params['bounding_boxes'])
    v['parameters']['bounding_boxes'] = box_list
    with open(fname,'w') as f:
        pickle.dump(v,f)
    print 'STATUS: Finished writing to file',fname
