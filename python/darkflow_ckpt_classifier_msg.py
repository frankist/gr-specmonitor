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

import os
import shutil
import numpy as np
from gnuradio import gr
import pmt
import cv2
import time

from darkflow_tools.darkflow_ckpt_classifier import *
from darkflow_statistics_collector import *

class darkflow_ckpt_classifier_msg(gr.basic_block):
    """
    docstring for block darkflow_ckpt_classifier_msg
    """
    def __init__(self, yaml_config, fftsize, threshold = 0.6):
        self.yaml_file = yaml_config
        self.fftsize = fftsize
        self.threshold = threshold

        self.classifier = DarkflowCkptClassifier(self.yaml_file,self.threshold)

        model_params = self.classifier.cfg_obj.model_params()
        self.ncols = model_params['width']
        self.nrows = model_params['height']

        self.imgcv = np.zeros((self.nrows,self.ncols,3),np.uint8)
        self.last_result = []

        # set up radio
        gr.basic_block.__init__(self,
            name="darkflow_ckpt_classifier_msg",
            in_sig=None,
            out_sig=None)
        self.message_port_register_in(pmt.intern("gray_img"))
        self.set_msg_handler(pmt.intern("gray_img"), self.run_darkflow)
        self.message_port_register_out(pmt.intern('darkflow_out'))

        # statistics of the channel
        self.stats = darkflow_statistics_collector(period_print_sec=5)

        # save output for visualization
        self.output_saver = ClassifierOutputSaver(2)
        self.count_predictions = 0

    def run_darkflow(self, msg):
        self.count_predictions += 1
        if np.mod(self.count_predictions,5)!=0: # skip
            return
        # convert message to numpy array
        u8img = pmt.pmt_to_python.uvector_to_numpy(msg).reshape(self.nrows,self.fftsize)

        self.imgcv[:,0:self.fftsize,0] = u8img
        self.imgcv[:,0:self.fftsize,1] = u8img
        self.imgcv[:,0:self.fftsize:,2] = u8img
        detected_boxes = self.classifier.classify(self.imgcv)
        self.last_result = detected_boxes

        # write a file with boxes output
        if self.output_saver is not None:
            self.output_saver.save_output(self.classifier,self.imgcv)

        for box in detected_boxes:
            d = pmt.make_dict()
            # d = pmt.dict_add(d, pmt.intern('tstamp'), pmt.from_long(self.img_tstamp))
            for k,v in box.items():
                if k=='topleft' or k=='bottomright':
                    pmt_val = pmt.make_dict()
                    pmt_val = pmt.dict_add(pmt_val,
                                        pmt.intern('x'),
                                        pmt.from_long(v['x']))
                    pmt_val = pmt.dict_add(pmt_val,
                                        pmt.intern('y'),
                                        pmt.from_long(v['y']))
                elif k=='confidence':
                    pmt_val = pmt.from_float(float(v))
                elif k=='label':
                    pmt_val = pmt.string_to_symbol(v)
                else:
                    raise NotImplementedError('Did not expect parameter {}'.format(k))
                d = pmt.dict_add(d, pmt.intern(k), pmt_val)
            self.stats.process_darkflow_results(d)
            self.message_port_pub(pmt.intern('darkflow_out'),d)

class ClassifierOutputSaver(object):
    def __init__(self,period=2):
        self.last_save_tstamp = time.time()
        self.period = period
        self.num_img_writes = 0
        self.save_folder = os.path.expanduser('~/tmp/classifier_output')
        if os.path.exists(self.save_folder):
            shutil.rmtree(self.save_folder)
        os.mkdir(self.save_folder)

    def save_output(self,classifier,imgcv):
        if (time.time()-self.last_save_tstamp)>self.period:
            # enough time has passed
            fname = os.path.join(self.save_folder,'record_tmp{}.png'.format(self.num_img_writes))
            newim,boxes=classifier.classify2(imgcv,True,True)
            print 'boxes:',boxes
            print('Gonna save image to file {}'.format(fname))
            cv2.imwrite(fname, newim)
            self.num_img_writes += 1
            self.last_save_tstamp = time.time()
