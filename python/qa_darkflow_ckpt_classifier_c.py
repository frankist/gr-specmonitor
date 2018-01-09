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
from darkflow_ckpt_classifier_c import darkflow_ckpt_classifier_c
import numpy as np
import cv2
import os
from PIL import Image
import matplotlib.pyplot as plt

from labeling_framework.sig_format import pkl_sig_format
from labeling_framework.sig_format import sig_data_access as sda
from labeling_framework.data_representation import spectrogram

class qa_darkflow_ckpt_classifier_c (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t(self):
        imgfilename = './tests/deep_learning/dataset/JPEGImages/data_wifi_0_0_0_0_0.jpg'
        # yaml_file = '../../scripts/deep_learning/yolo_train.yml' # FIXME
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml' # FIXME
        # print 'this is the cwd:',os.path.abspath('./')

        # read image
        imgcv = cv2.imread(imgfilename)
        imgnp = np.asarray(imgcv) # 104,104,3
        imgnp_gray = np.mean(imgnp, axis=2) # 104,104
        imgnp = np.array(imgnp_gray.flatten(), np.float32)
        imgtuple = tuple([float(i) for i in imgnp])
        plt.imshow(imgnp_gray)
        plt.show()

        # create blocks
        vector_source = blocks.vector_source_f(imgtuple,True)
        head = blocks.head(gr.sizeof_float, 104*104)
        toparallel = blocks.stream_to_vector(gr.sizeof_float, 104)
        classifier = darkflow_ckpt_classifier_c(yaml_file)

        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,classifier)

        self.tb.run()

        # check data
        self.assertEqual(len(classifier.last_result),5)
        for b in classifier.last_result:
            self.assertEqual(b['label'],'wifi')
        print 'detected boxes:',classifier.last_result

    def test_002_t(self):
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml'
        pkl_file = '~/Dropbox/Programming/deep_learning/test_data/qa_darkflow/data_wifi_0_0_0_0.pkl' # FIXME

        freader = pkl_sig_format.WaveformPklReader(os.path.expanduser(pkl_file))
        x = freader.read_section()
        stage_data = freader.data()
        spec_metadata = sda.get_stage_derived_parameter(stage_data,'subsection_spectrogram_img_metadata')

        # convert x to spectrogram
        Sxx = spec_metadata[0].image_data(x)
        Sxx_img = np.zeros((104,104))
        Sxx_img[0:Sxx.shape[0],0:Sxx.shape[1]] = Sxx
        Sxx_bytes = np.uint8(Sxx_img*255)

        tmp_path = os.path.expanduser('~/tmp/test.png')#.jpeg')
        cv2.imwrite(tmp_path, Sxx_bytes) #[int(cv2.IMWRITE_JPEG_QUALITY), 100])
        # im = Image.fromarray(Sxx_bytes)
        # im.save(os.path.expanduser('~/tmp/test.jpeg'),'JPEG')
        imgnp_gray = cv2.imread(tmp_path,0)
        # imgnp_gray = cv2.cvtColor(imgcv,cv2.COLOR_BGR2GRAY)
        # imgnp = np.asarray(imgcv) # 104,104,3
        # imgnp_gray = np.mean(imgnp, axis=2) # 104,104
        Sxxflat = np.array(imgnp_gray.flatten(), np.float32) #Sxx_img.flatten()
        imgtuple = tuple([float(i) for i in Sxxflat])

        print 'this is the compression diff:', np.mean(np.abs(imgnp_gray-Sxx_bytes)**2)
        plt.imshow(imgnp_gray)#Sxx_img)
        plt.show()

        # create blocks
        vector_source = blocks.vector_source_f(imgtuple, True)
        head = blocks.head(gr.sizeof_float, 104*104)
        toparallel = blocks.stream_to_vector(gr.sizeof_float, 104)
        classifier = darkflow_ckpt_classifier_c(yaml_file)

        # make flowgraph
        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,classifier)

        self.tb.run()

        # check data
        print 'detected boxes:',classifier.last_result
        self.assertEqual(len(classifier.last_result),5)
        for b in classifier.last_result:
            self.assertEqual(b['label'],'wifi')

if __name__ == '__main__':
    gr_unittest.run(qa_darkflow_ckpt_classifier_c, "qa_darkflow_ckpt_classifier_c.xml")
