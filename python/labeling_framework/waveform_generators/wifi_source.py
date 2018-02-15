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
import cPickle as pickle
import time

import sys
sys.path.append(
    os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))
from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from wifi_phy_hier import wifi_phy_hier  # grc-generated hier_block
import foo
import ieee802_11
import pmt
import specmonitor

# labeling_framework package
import waveform_generator_utils as wav_utils
from waveform_launcher import SignalGenerator
from ..labeling_tools.parametrization import random_generator
from ..data_representation import timefreq_box
from ..core import SignalDataFormat as sdf
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

class GrWifiFlowgraph(gr.top_block):#gr_qtgui_utils.QtTopBlock):
    encoding_labels = [
        "BPSK 1/2", "BPSK 3/4", "QPSK 1/2", "QPSK 3/4", "16QAM 1/2",
        "16QAM 3/4", "64QAM 2/3", "64QAM 3/4"
    ]

    def __init__(self,
                 n_written_samples,
                 n_offset_samples,
                 encoding=0,
                 pdu_length=500,
                 pad_interval=1000,
                 linear_gain=1.0):
        super(GrWifiFlowgraph, self).__init__()

        # params
        self.n_written_samples = int(n_written_samples)
        self.n_offset_samples = int(n_offset_samples) if n_offset_samples is not None else np.random.randint(0,self.n_written_samples)
        self.linear_gain = float(linear_gain)
        self.pdu_length = pdu_length  # size of the message passed to the WiFi [1,1500]
        assert isinstance(encoding, (int, str))
        self.encoding = encoding if isinstance(encoding,int) else GrWifiFlowgraph.encoding_labels.index(encoding)
        if isinstance(pad_interval,tuple):
            self.distname = pad_interval[0]
            self.pad_interval = pad_interval[1]
        else:
            self.distname = 'constant'
            self.pad_interval = tuple(pad_interval)

        # phy
        self.wifi_phy_hier = wifi_phy_hier(
            bandwidth=20e6,  # NOTE: used by the Rx only
            chan_est=0,  # NOTE: used by the Rx only
            encoding=self.encoding,
            frequency=5.89e9,  # NOTE: Rx only
            sensitivity= 0.56,  # NOTE: Rx only
        )
        self.packet_pad = specmonitor.foo_random_burst_shaper_cc(
            False,
            False,
            0,
            self.distname,
            self.pad_interval,
            100, [0])
        self.packet_pad.set_min_output_buffer(
            1000000)
        # self.foo_packet_pad2 = foo.packet_pad2(
        #     False, # Debug
        #     False, 0.01,
        #     100, # Before padding
        #     self.pad_interval)  # After padding
        # self.foo_packet_pad2.set_min_output_buffer(
        #     96000)  # CHECK: What does this do?
        # # self.time_plot = gr_qtgui_utils.make_time_sink_c(1024, 20.0e6, "", 1)

        self.blocks_null_source = blocks.null_source(gr.sizeof_gr_complex * 1)
        self.skiphead = blocks.skiphead(gr.sizeof_gr_complex, self.n_offset_samples)
        self.head = blocks.head(gr.sizeof_gr_complex, self.n_written_samples)
        self.dst = blocks.vector_sink_c()
        # dst = blocks.file_sink(gr.sizeof_gr_complex,args['targetfolder']+'/tmp.bin')

        # mac
        self.ieee802_11_mac = ieee802_11.mac(
            ([0x23, 0x23, 0x23, 0x23, 0x23, 0x23]),
            ([0x42, 0x42, 0x42, 0x42, 0x42, 0x42]),
            ([0xff, 0xff, 0xff, 0xff, 0xff, 255]))
        pmt_message = pmt.intern("".join("x" for i in range(self.pdu_length)))
        # self.message_strobe = foo.periodic_msg_source(pmt_message,
        #                                               self.interval_ms, self.num_msg, True, False)
        self.message_strobe = blocks.message_strobe(
            pmt.intern("".join("x" for i in range(self.pdu_length))),
            0)  # NOTE: This sends a message periodically
        # self.message_debug = blocks.message_debug()

        self.setup_flowgraph()

    def setup_flowgraph(self):
        ##################################################
        # Connections
        ##################################################
        # self.msg_connect((self.blocks_message_strobe,'strobe'),(self.message_debug,'print'))
        self.msg_connect((self.message_strobe, 'strobe'),
                         (self.ieee802_11_mac, 'app in'))
        self.msg_connect((self.ieee802_11_mac, 'phy out'),
                         (self.wifi_phy_hier, 'mac_in'))
        self.msg_connect((self.wifi_phy_hier, 'mac_out'),
                         (self.ieee802_11_mac, 'phy in'))
        self.connect((self.blocks_null_source, 0),
                     (self.wifi_phy_hier, 0))  # no reception

        self.connect((self.wifi_phy_hier, 0), self.packet_pad)
        # self.connect((self.wifi_phy_hier, 0), self.time_plot)
        self.connect(self.packet_pad, self.skiphead)
        self.connect(self.skiphead, self.head)
        self.connect(self.head, self.dst)

    def run(self): #NOTE: The message probe does not stop the block, so I had to find a work around
        self.start()
        # while self.message_strobe.is_running():
        #     time.sleep(0.01)
        while self.dst.nitems_read(0)<self.n_written_samples:
            time.sleep(0.01)
        self.stop()
        self.wait()

def run(args):
    d = args['parameters']
    # wav_utils.print_params(d,__name__)

    # create Wifi block
    tb = GrWifiFlowgraph(
        d['number_samples'],
        d.get('number_offset_samples',None),
        encoding=d['encoding'],
        pdu_length=d['pdu_length'],
        pad_interval=d['pad_interval'])

    logger.info('Starting GR waveform generator script for Wifi')
    tb.run()
    logger.debug('GR script finished')

    # output signal
    x = np.array(tb.dst.data())

    # create a StageSignalData structure
    stage_data = wav_utils.set_derived_sigdata(x,args,True)
    metadata = stage_data.derived_params['spectrogram_img']
    tfreq_boxes = metadata.tfreq_boxes
    timefreq_box.set_boxes_mag2(x,tfreq_boxes)

    # randomly scale and normalize boxes magnitude
    frame_mag2_gen = random_generator.load_generator(args['parameters'].get('frame_mag2',1))
    tfreq_boxes = wav_utils.random_scale_mag2(tfreq_boxes,frame_mag2_gen)
    tfreq_boxes = wav_utils.normalize_mag2(tfreq_boxes)
    y = wav_utils.set_signal_mag2(x,tfreq_boxes)
    metadata.tfreq_boxes = tfreq_boxes
    stage_data.samples = y

    # create a MultiStageSignalData structure and save it
    v = sdf.MultiStageSignalData()
    v.set_stage_data(stage_data)
    v.save_pkl()

class WifiGenerator(SignalGenerator):
    @staticmethod
    def run(args):
        while True:
            try:
                run(args)
            except RuntimeError, e:
                logger.warning('Failed to generate the waveform data for WiFi. Going to rerun. Arguments: {}'.format(args))
                continue
            except KeyError, e:
                logger.error('The input arguments do not seem valid. They were {}'.format(args))
                raise
            break

    @staticmethod
    def name():
        return 'wifi'

if __name__ == '__main__':
    logger.basicConfig(level='DEBUG')
    targetfile = '~/tmp/out.pkl'
    args = {
        'parameters': {
            'number_samples': 100000,
            'number_offset_samples': 0,
            'encoding': 0,
            'pdu_length': 500,
            'pad_interval': 5000,
        },
        'targetfilename': targetfile,
        'stage_name': 'waveform'
    }
    targetfile = os.path.expanduser(targetfile)
    run_wifi_source(args)
    import pkl_sig_format
    dat = pkl_sig_format.WaveformPklReader(targetfile)
    x = dat.read_section()
    plt.plot(np.abs(x))
    plt.show()
    os.remove(targetfile)
