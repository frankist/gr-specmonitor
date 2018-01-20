#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2018 <+YOU OR YOUR COMPANY+>.
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

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from gnuradio import fft
import specmonitor_swig as specmonitor
# from spectrogram_img_c import spectrogram_img_c
import numpy as np
from scipy import signal
import os
import pmt
import matplotlib.pyplot as plt

from labeling_framework.sig_format import pkl_sig_format
from labeling_framework.sig_format import sig_data_access as sda
from labeling_framework.data_representation import spectrogram

class qa_spectrogram_img_c (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml'
        pkl_file = '~/Dropbox/Programming/deep_learning/test_data/qa_darkflow/data_wifi_0_0_0_0_0.pkl' # FIXME

        freader = pkl_sig_format.WaveformPklReader(os.path.expanduser(pkl_file))
        x = freader.read_section()
        stage_data = freader.data()
        spec_metadata = sda.get_stage_derived_parameter(stage_data,'subsection_spectrogram_img_metadata')

        Sxx = spec_metadata[0].image_data(x)
        Sxx_bytes = np.uint8(Sxx*255)

        section_bounds = spec_metadata[0].section_bounds
        xsection = x[section_bounds[0]::] # let the block head finish the section
        xtuple = tuple([complex(i) for i in xsection])

        vector_source = blocks.vector_source_c(xtuple, True)
        head = blocks.head(gr.sizeof_gr_complex, 64*104*10)
        toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, 64)
        fftblock = fft.fft_vcc(64,True,signal.get_window(('tukey',0.25),64),True)
        spectroblock = specmonitor.spectrogram_img_c(64, 104, 104, 10, True)
        tostream = blocks.vector_to_stream(gr.sizeof_gr_complex, 64)
        dst = blocks.vector_sink_c()
        pdu_debug = blocks.message_debug()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,fftblock)
        self.tb.connect(fftblock,spectroblock)
        self.tb.connect(fftblock,tostream)
        # self.tb.connect(tostream,spectroblock)
        self.tb.connect(tostream,dst)

        self.tb.msg_connect(spectroblock, "imgcv", pdu_debug, "store")

        self.tb.run()
        xout = dst.data()
        vecbytes_pmt = pdu_debug.get_message(0)
        imgu8 = pmt.pmt_to_python.uvector_to_numpy(vecbytes_pmt).reshape(104,64)

        # inspired by https://lists.gnu.org/archive/html/discuss-gnuradio/2013-08/msg00094.html
        # vecbytes = pmt.u8vector_elements(vecbytes_pmt)#,64*104)
        # vecbytes2 = pmt.serialize_str(vecbytes_pmt)
        # imgsize = 104*64
        # self.assertEqual(np.fromstring(vecbytes2,np.uint8).size, imgsize+8)
        # imgu8 = np.fromstring(vecbytes2,np.uint8)[8::].reshape(104,64)
        # NOTE: u8vector_elements creates a vector of long type

        self.assertEqual(len(xout),104*64*10)
        self.assertEqual(len(pmt.u8vector_elements(vecbytes_pmt)),104*64)
        self.assertEqual(imgu8.size,104*64)
        diff = np.sum(np.abs(np.array(Sxx_bytes,np.float32)-np.array(imgu8,np.float32)))
        print 'diff:',diff
        self.assertTrue(diff<2)
        self.assertEqual(imgu8.dtype,np.uint8)

        # plt.imshow(imgu8)
        # plt.imshow(Sxx_bytes)
        # plt.imshow(Sxx_bytes-imgu8)
        # plt.show()


if __name__ == '__main__':
    gr_unittest.run(qa_spectrogram_img_c, "qa_spectrogram_img_c.xml")
