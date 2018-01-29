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
import os
import pickle
# import matplotlib.pyplot as plt

# gnuradio dependencies
from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog

# labeling_framework dependencies
from waveform_generator_utils import *
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def run(args):
    gr_waveform_map = {'square':analog.GR_SQR_WAVE,'saw':analog.GR_SAW_WAVE}
    d = args['parameters']
    #skip_samples =
    amp = 1.0
    offset = 0
    # print_params(d)
    wf = gr_waveform_map[d['waveform']]

    tb = gr.top_block()

    source = analog.sig_source_f(d['sample_rate'],wf,
                                    d['frequency'],amp,offset)
    float2cplx = blocks.float_to_complex()
    head = blocks.head(gr.sizeof_gr_complex, int(d['number_samples']))
    dst = blocks.vector_sink_c()
    # dst = blocks.file_sink(gr.sizeof_gr_complex,args['targetfolder']+'/tmp.bin')

    tb.connect(source,float2cplx)
    tb.connect(float2cplx,head)
    tb.connect(head,dst)

    logger.info('Starting GR waveform generator script for waveform %s',d['waveform'])
    tb.run()
    logger.debug('GR script finished')

    # TODO: read file to insert bounding boxes and params
    logger.info('Starting GR waveform generator script for sig source')
    gen_data = np.array(dst.data())
    logger.debug('GR script finished')

    v = transform_IQ_to_sig_data(gen_data,args)

    # save file
    v.save_pkl()
    # fname=os.path.expanduser(args['targetfilename'])
    # with open(fname,'wb') as f:
    #     pickle.dump(v,f)
    # logger.debug('Finished writing to file %s', fname)
