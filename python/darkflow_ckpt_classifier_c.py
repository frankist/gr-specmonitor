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

import numpy as np
from gnuradio import gr
import pmt
import cv2

from darkflow_tools.darkflow_ckpt_classifier import *
from labeling_framework.data_representation import spectrogram

class darkflow_ckpt_classifier_c(gr.sync_block):
    """
    docstring for block darkflow_ckpt_classifier_c
    """
    def __init__(self, yaml_config, vlen, cancel_DCoffset=True, avgsize = 1):
        self.yaml_file = yaml_config
        self.classifier = DarkflowCkptClassifier(self.yaml_file)
        model_params = self.classifier.cfg_obj.model_params()
        self.ncols = model_params['width']
        self.nrows = model_params['height']
        self.vlen = vlen
        self.count = 0
        self.imgnp = np.zeros((self.nrows,self.vlen),np.float32)
        self.imgcv = np.zeros((self.nrows,self.ncols,3),np.uint8)
        gr.sync_block.__init__(self,
            name="darkflow_ckpt_classifier_c",
            in_sig = [(np.float32,self.vlen)],
            out_sig = None)#[])#np.complex64)
        self.message_port_register_out(pmt.intern('msg_out'))
        # FIXME: ncols is different than vector size!
        self.nsamplesread = 0
        self.img_tstamp = 0
        self.avgsize = avgsize
        self.countavg = 0
        self.cancel_DCoffset = cancel_DCoffset
        self.last_result = []

    def work(self, input_items, output_items):
        in0 = input_items[0]
        #out = output_items[0]
        for idx in range(in0.shape[0]):
            self.imgnp[self.count,:] += in0[idx,:]
            self.countavg+=1
            if self.countavg==self.avgsize:
                self.count += 1
                self.countavg=0
            self.nsamplesread += len(in0[idx,:])
            if self.count == self.nrows:
                Sxx = spectrogram.normalize_spectrogram(self.imgnp)#/self.avgsize)
                if self.cancel_DCoffset:
                    pwr_min = np.min(Sxx)
                    Sxx[:,Sxx.shape[1]/2] = pwr_min # FIXME
                self.imgcv[:,0:self.vlen,0] = np.uint8(Sxx*255)
                self.imgcv[:,:,1] = self.imgcv[:,:,0]
                self.imgcv[:,:,2] = self.imgcv[:,:,0]
                self.count = 0
                self.imgnp[:] = 0
                detected_boxes = self.classifier.classify(self.imgcv)
                self.last_result = detected_boxes
                for box in detected_boxes:
                    d = pmt.make_dict()
                    d = pmt.dict_add(d, pmt.intern('tstamp'), pmt.from_long(self.img_tstamp))
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
                    # print 'gonna send:',pmt.write_string(d)
                    self.message_port_pub(pmt.intern('msg_out'),d)
                # self.message_port_pub(pmt.intern('boxes'), pmt.intern(detected_boxes))
                self.img_tstamp += int(self.vlen*self.nrows)

        return len(input_items[0])

