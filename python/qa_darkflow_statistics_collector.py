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
from darkflow_statistics_collector import darkflow_statistics_collector
from darkflow_ckpt_classifier_msg import darkflow_ckpt_classifier_msg
import os
import numpy as np
from scipy import signal
import time

from labeling_framework.sig_format import pkl_sig_format
from labeling_framework.sig_format import sig_data_access as sda

class qa_darkflow_statistics_collector (gr_unittest.TestCase):

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

        section_bounds = spec_metadata[0].section_bounds
        xsection = x[section_bounds[0]::] # let the block head finish the section
        xtuple = tuple([complex(i) for i in xsection])

        vector_source = blocks.vector_source_c(xtuple, True)
        head = blocks.head(gr.sizeof_gr_complex, 64*104*10)
        toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, 64)
        fftblock = fft.fft_vcc(64,True,signal.get_window(('tukey',0.25),64),True)
        spectroblock = specmonitor.spectrogram_img_c(64, 104, 104, 10, True)
        classifier = darkflow_ckpt_classifier_msg(yaml_file, 64)
        statsblock = darkflow_statistics_collector()
        tostream = blocks.vector_to_stream(gr.sizeof_gr_complex, 64)
        dst = blocks.vector_sink_c()

        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,fftblock)
        self.tb.connect(fftblock,spectroblock)
        self.tb.connect(fftblock,tostream)
        self.tb.connect(tostream,dst)
        self.tb.msg_connect(spectroblock, "imgcv", classifier, "gray_img")
        self.tb.msg_connect(classifier, "darkflow_out", statsblock, "msg_in")

        # GNURadio has some bug when using streams. It hangs
        # self.tb.run()
        self.tb.start()
        while dst.nitems_read(0) < 104*64*10:
            time.sleep(0.01)
        self.tb.stop()
        self.tb.wait()
        xout = dst.data()
        yolo_result = classifier.last_result

        self.assertEqual(len(xout),104*64*10)
        self.assertTrue(len(classifier.last_result)!=0)

        stb = classifier.stats # FIXME: The block statsblock does not receive any PDU!!!
        self.assertTrue(len(stb.stats)>0)
        # print 'these are the collected statistics:',stb.stats
        self.assertTrue(stb.stats['wifi']==4)
        self.assertTrue(stb.label_mode()=='wifi')

if __name__ == '__main__':
    gr_unittest.run(qa_darkflow_statistics_collector, "qa_darkflow_statistics_collector.xml")
