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
import sys
import pickle
from bounding_box import *

def print_params(params):
    print 'sig_source_c starting'
    for k,v in params.iteritems():
        print k,v,type(v)

def run_signal_source(args):
    gr_waveform_map = {'square':analog.GR_SQR_WAVE,'saw':analog.GR_SAW_WAVE}
    d = args['parameters']
    #skip_samples =
    amp = 1.0
    offset = 0
    # print_params(d)
    wf = gr_waveform_map[d['waveform']]

    tb = gr.top_block()

    source = analog.sig_source_c(d['sample_rate'],wf,
                                    d['frequency'],amp,offset)
    head = blocks.head(gr.sizeof_gr_complex, int(d['number_samples']))
    dst = blocks.vector_sink_c()
    # dst = blocks.file_sink(gr.sizeof_gr_complex,args['targetfolder']+'/tmp.bin')

    tb.connect(source,head)
    tb.connect(head,dst)

    print 'STATUS: Starting GR waveform generator script'
    tb.run()
    print 'STATUS: GR script finished'

    # TODO: read file to insert bounding boxes and params
    gen_data = np.array(dst.data())
    print 'STATUS: Going to compute Bounding Boxes'
    box_list = compute_bounding_box(gen_data)
    print 'STATUS: Finished computing the Bounding Boxes'
    # print [(b.time_bounds,b.freq_bounds) for b in box_list]

    v = {'parameters':args['parameters'],'IQsamples':gen_data}
    v['parameters']['bounding_boxes'] = box_list
    fname=args['targetfilename']
    with open(fname,'wb') as f:
        pickle.dump(v,f)
    print 'STATUS: Finished writing to file',fname

if __name__ == '__main__':
    args = pickle.loads(sys.argv[1])
    run_square_source(args)
