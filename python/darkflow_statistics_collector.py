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

import numpy
from gnuradio import gr
import time
import pmt

class darkflow_statistics_collector(gr.basic_block):
    """
    docstring for block darkflow_statistics_collector
    """
    def __init__(self,period_print_sec = 10):
        gr.basic_block.__init__(self,
                                name="darkflow_ckpt_classifier_msg",
                                in_sig=None,
                                out_sig=None)
        self.message_port_register_in(pmt.intern('msg_in'))
        self.set_msg_handler(pmt.intern('msg_in'), self.process_darkflow_results)
        self.stats = {}
        self.print_period_sec = period_print_sec
        self.last_print_tstamp = time.time()-self.print_period_sec

    def process_darkflow_results(self,msg):
        # print 'detected box:', msg
        label = pmt.symbol_to_string(pmt.dict_ref(msg,pmt.intern('label'),pmt.PMT_NIL))
        if label not in self.stats.keys():
            self.stats[label] = 0
        self.stats[label] += 1

        if (time.time()-self.last_print_tstamp)>self.print_period_sec:
            print 'stats:',self.stats
            kmax = self.label_mode()
            print 'STATUS: The channel contains mostly',kmax,'signals'
            self.last_print_tstamp = time.time()

    def label_mode(self):
        v=list(self.stats.values())
        k=list(self.stats.keys())
        return k[v.index(max(v))]
