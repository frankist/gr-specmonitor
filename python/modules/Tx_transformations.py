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
import preamble_utils

def print_params(params):
    print 'sig_source_c starting'
    for k,v in params.iteritems():
        print k,v,type(v)

def generate_section_partitions(section_size,guard_band,num_sections):
    return ((guard_band+i*section_size,guard_band+(i+1)*section_size) for i in range(num_sections))

def compute_new_bounding_boxes(time_offset,section_size,freq_offset,box_list):
    boi = intersect_boxes_with_section(box_list,(time_offset,time_offset+section_size))
    boi_offset = add_offset(boi,-time_offset,freq_offset)
    return list(boi_offset)

def partition_boxes_into_sections(box_list,section_size,guard_band,num_sections):
    section_ranges = generate_section_partitions(section_size,guard_band,num_sections)
    return [list(intersect_and_offset_box(box_list,s)) for s in section_ranges]

def apply_framing_and_offsets(args):
    params = args['parameters']
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']

    ### Read parameters
    time_offset = params['time_offset']
    section_size = params['section_size']
    num_sections = params['num_sections']
    noise_voltage = 0#params.get('noise_voltage',0)
    freq_offset = params.get('frequency_offset',0)
    soft_gain = params.get('soft_gain',1)
    epsilon = params.get('epsilon',1)
    taps = None
    seed = 0
    num_samples = num_sections*section_size
    hist_len = 3 # compensate for block history# channel is hier block with taps in it

    ### Create preamble and frame structure
    lvl2_diff_len = len(random_sequence.maximum_length_sequence(13))
    pseq_len = [13,61]
    guard_len = 5
    awgn_guard_len = 100
    pparams = preamble_utils.generate_preamble_type2(pseq_len,lvl2_diff_len)
    fparams = preamble_utils.frame_params(pparams,guard_len,awgn_guard_len,section_size)
    sframer = preamble_utils.SignalFramer(fparams)

    ### Read IQsamples
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    twin = (time_offset-guard_len-hist_len,time_offset+num_samples+guard_len)
    xsections_with_hist = freader.read_section(twin[0],twin[1])
    prev_params = freader.parameters()

    ### Create GR flowgraph that picks read samples, applies freq_offset, scaling, and stores in a vector_sink
    tb = gr.top_block()
    source = blocks.vector_source_c(xsections_with_hist, True)
    soft_amp = blocks.multiply_const_cc(np.sqrt(soft_gain)+0*1j)
    channel = channels.channel_model(noise_voltage,freq_offset)
    assert len(channel.taps())+1==hist_len
    head = blocks.head(gr.sizeof_gr_complex,xsections_with_hist.size-hist_len)
    dst = blocks.vector_sink_c()

    tb.connect(source,soft_amp)
    tb.connect(soft_amp,channel)
    tb.connect(channel,head)
    tb.connect(head,dst)

    print 'STATUS: Starting GR waveform generator script'
    tb.run()
    print 'STATUS: GR script finished'

    gen_data = np.array(dst.data())
    xsections = xsections_with_hist[hist_len::]
    # plt.plot(np.abs(gen_data))
    # plt.plot(np.abs(xsections),'r')
    # plt.show()
    assert gen_data.size==xsections.size

    ### Create preamble structure and frame the signal
    y,section_bounds = sframer.frame_signal(gen_data,num_sections)

    # print 'boxes:',[b.__str__() for b in freader.data()['bounding_boxes']]
    box_list = compute_new_bounding_boxes(time_offset,num_samples,freq_offset,freader.data()['bounding_boxes'])
    section_boxes = partition_boxes_into_sections(box_list,section_size,guard_band,num_sections)
    # print 'these are the boxes divided by section:',[[b.__str__() for b in s] for s in section_boxes]
    v = {'parameters':prev_params,'IQsamples':y,'section_bounds':section_bounds,
         'section_bounding_boxes':section_boxes}
    
    v['parameters'][args['stage_name']] = params
    for i in range(num_sections):
        # plt.plot(y[section_bounds[i][0]:section_bounds[i][1]])
        # plt.plot(gen_data[guard_band+i*section_size:guard_band+(i+1)*section_size],'r:')
        # plt.show()
        assert np.all((y[section_bounds[i][0]:section_bounds[i][1]]-gen_data[guard_band+i*section_size:guard_band+(i+1)*section_size])<0.0001)

    with open(targetfilename,'w') as f:
        pickle.dump(v,f)
    print 'STATUS: Finished writing to file',targetfilename
