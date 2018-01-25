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
from darkflow_ckpt_classifier_c import darkflow_ckpt_classifier_c
import numpy as np
import cv2
import os
from PIL import Image
from scipy import signal
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
        imgfilename = './tests/deep_learning/dataset/Images/data_wifi_0_0_0_0_0.png'
        # yaml_file = '../../scripts/deep_learning/yolo_train.yml' # FIXME
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml' # FIXME
        # print 'this is the cwd:',os.path.abspath('./')

        # read image
        imgnp_gray = cv2.imread(imgfilename,0)
        # imgcv = cv2.imread(imgfilename)
        # imgnp = np.asarray(imgcv) # 104,104,3
        # imgnp_gray = np.mean(imgnp, axis=2) # 104,104
        imgnp = np.array(imgnp_gray.flatten(), np.float32)
        imgtuple = tuple([float(i) for i in imgnp])
        # plt.imshow(imgnp_gray)
        # plt.plot(imgnp_gray.flatten())
        # plt.show()
        self.assertEqual(len(imgtuple),104*104)

        # create blocks
        vector_source = blocks.vector_source_f(imgtuple,True)
        head = blocks.head(gr.sizeof_float, 104*104)
        toparallel = blocks.stream_to_vector(gr.sizeof_float, 104)
        classifier = darkflow_ckpt_classifier_c(yaml_file, 104, True)

        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,classifier)

        self.tb.run()

        # check data
        self.assertEqual(len(classifier.last_result),4)
        for b in classifier.last_result:
            self.assertEqual(b['label'],'wifi')
        print 'detected boxes:',classifier.last_result

    def test_002_t(self):
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml'
        pkl_file = '../../python/tests/deep_learning/dataset/Images/data_wifi_0_0_0_0_0.pkl' # FIXME

        freader = pkl_sig_format.WaveformPklReader(os.path.expanduser(pkl_file))
        x = freader.read_section()
        stage_data = freader.data()
        spec_metadata = sda.get_stage_derived_parameter(stage_data,'subsection_spectrogram_img_metadata')
        section_bounds = spec_metadata[0].section_bounds
        xsection = x[section_bounds[0]::] # let the block head finish the section

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

        # assert there was no compression loss
        self.assertAlmostEqual(np.mean(np.abs(imgnp_gray-Sxx_bytes)**2),0.0)
        # plt.imshow(imgnp_gray)#Sxx_img)
        # plt.show()

        # create blocks
        vector_source = blocks.vector_source_f(imgtuple, True)
        head = blocks.head(gr.sizeof_float, 104*104)
        toparallel = blocks.stream_to_vector(gr.sizeof_float, 104)
        classifier = darkflow_ckpt_classifier_c(yaml_file, 104, True)

        # make flowgraph
        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,classifier)

        self.tb.run()

        # check data
        print 'detected boxes:',classifier.last_result
        self.assertEqual(len(classifier.last_result),4)
        for b in classifier.last_result:
            self.assertEqual(b['label'],'wifi')

    def test_gr_preprocessing(self):
        yaml_file = '../../python/tests/qa_darkflow/yolo_model.yml'
        pkl_file = '~/Dropbox/Programming/deep_learning/test_data/qa_darkflow/data_wifi_0_0_0_0_0.pkl' # FIXME

        freader = pkl_sig_format.WaveformPklReader(os.path.expanduser(pkl_file))
        x = freader.read_section()
        stage_data = freader.data()
        spec_metadata = sda.get_stage_derived_parameter(stage_data,'subsection_spectrogram_img_metadata')

        # convert x to spectrogram
        Sxx = spec_metadata[0].image_data(x)
        Sxx_img = np.zeros((104,104),np.float32)
        Sxx_img[0:Sxx.shape[0],0:Sxx.shape[1]] = Sxx
        Sxx_bytes = np.uint8(Sxx_img*255)

        section_bounds = spec_metadata[0].section_bounds
        xsection = x[section_bounds[0]::] # let the block head finish the section
        xtuple = tuple([complex(i) for i in xsection])

        # create blocks
        vector_source = blocks.vector_source_c(xtuple, True)
        head = blocks.head(gr.sizeof_gr_complex, 64*104*10)
        toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, 64)
        # fftblock = fft.fft_vcc(64,True,fft.window.rectangular(64),True)
        fftblock = fft.fft_vcc(64,True,signal.get_window(('tukey',0.25),64),True)
        mag2 = blocks.complex_to_mag_squared(64)
        # avg = blocks.moving_average_ff(104,1.0/104,104)
        classifier = darkflow_ckpt_classifier_c(yaml_file, 64, True, 10)
        dst1 = blocks.vector_sink_c()
        dst2 = blocks.vector_sink_c(64)
        dst3 = blocks.vector_sink_f(64)

        # make flowgraph
        self.tb.connect(vector_source,head)
        self.tb.connect(head,toparallel)
        self.tb.connect(toparallel,fftblock)
        self.tb.connect(fftblock,mag2)
        self.tb.connect(mag2,classifier)

        self.tb.connect(head,dst1)
        self.tb.connect(fftblock,dst2)
        self.tb.connect(mag2,dst3)

        self.tb.run()
        xout = np.array(dst1.data(),np.complex64)
        xfft = np.array(dst2.data(),np.complex64)
        xmag2 = np.array(dst3.data(),np.float32)
        im = classifier.imgcv[:,:,0]

        # check output data correctness
        self.assertEqual(xout.size,104*64*10)
        self.assertComplexTuplesAlmostEqual(xsection[0:len(xout)],xout)

        # check all the steps for spectrogram creation are correct
        sxx_xout = spectrogram.compute_spectrogram(xout,64)
        # sxx_xout = spectrogram.make_spectrogram_image(xout,{'fftsize':64,'cancel_DC_offset':True})
        sxx_xout_avg = spectrogram.time_average_Sxx(sxx_xout,10,10)
        sxx_xout_avg = spectrogram.normalize_spectrogram(sxx_xout_avg)
        sxx_xout_avg = spectrogram.cancel_spectrogram_DCoffset(sxx_xout_avg)
        sxx_xout_bytes = np.zeros((104,104),np.uint8)
        sxx_xout_bytes[:,0:64] = np.uint8(sxx_xout_avg*255)
        self.assertAlmostEqual(np.mean(np.abs(sxx_xout_bytes-Sxx_bytes)**2),0)
        self.assertAlmostEqual(np.mean(np.abs(sxx_xout_bytes-im)**2),0)

        sxx_xfft = np.abs(xfft.reshape((104*10,64)))**2
        sxx_xfft_avg = spectrogram.time_average_Sxx(sxx_xfft,10,10)
        sxx_xfft_avg = spectrogram.normalize_spectrogram(sxx_xfft_avg)
        sxx_xfft_avg = spectrogram.cancel_spectrogram_DCoffset(sxx_xfft_avg)
        sxx_xfft_bytes = np.zeros((104,104),np.uint8)
        sxx_xfft_bytes[:,0:64] = np.uint8(sxx_xfft_avg*255)
        self.assertAlmostEqual(np.mean(np.abs(sxx_xfft_bytes-Sxx_bytes)**2),0)
        self.assertAlmostEqual(np.mean(np.abs(sxx_xfft_bytes-im)**2),0)

        # xoutwin = xout[0:64]*signal.get_window(('tukey',0.25),64)
        # xfft_debug = np.fft.fftshift(np.fft.fft(xoutwin))

        print 'detected boxes:',classifier.last_result
        self.assertEqual(len(classifier.last_result),4)
        for b in classifier.last_result:
            self.assertEqual(b['label'],'wifi')

if __name__ == '__main__':
    gr_unittest.run(qa_darkflow_ckpt_classifier_c, "qa_darkflow_ckpt_classifier_c.xml")
