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

def run_signal_source(args):
    gr_waveform_map = {'square':analog.GR_SQR_WAVE,'saw':analog.GR_SAW_WAVE}
    d = args['parameters']
    #skip_samples =
    amp = 1.0
    offset = 0

    tb = gr.top_block()

    source = analog.signal_source_c(d['sample_rate'],gr_waveform_map[d['waveform']],
                                    d['frequency'],amp,offset)
    head = blocks.head(gr.sizeof_gr_complex, d['num_samples'])
    dst = blocks.file_sink(gr.sizeof_gr_complex,args['result_filename'])

    tb.connect(source,head)
    tb.connect(head,dst)

    tb.run()

    # TODO: read file to insert bounding boxes and params
    # write bounding boxes
    # write parameters
    # write samples

if __name__ == '__main__':
    args = pickle.loads(sys.argv[1])
    run_square_source(args)
