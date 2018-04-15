#!/usr/bin/env python

from gnuradio import gr
from gnuradio import blocks
from gnuradio import fft
from gnuradio import uhd
from scipy import signal
import argparse

from specmonitor import spectrogram_img_c
from specmonitor import darkflow_tcp_client

radio_metadata = {
    'frequency':2.3e9,
    'ncols':104,
    'nrows':104,
    'n_avgs':80,
    'sample_rate':23.04e6
}

class DarkflowClientFlowGraph(gr.top_block):
    def __init__(self,yaml_config='',addr=('127.0.0.1',9999),freq=None):
        super(DarkflowClientFlowGraph, self).__init__()

        # params
        radio_metadata['frequency'] = freq
        self.yaml_config = yaml_config
        sample_rate = 23.04e6
        centre_freq = freq
        gaindB = 21#30
        fftsize = 104
        n_avgs = radio_metadata['n_avgs']
        ncols = radio_metadata['ncols']
        nrows = radio_metadata['nrows']

        # flowgraph blocks
        self.usrp_source = uhd.usrp_source(
            ",".join(("", "")),
            uhd.stream_args(
                cpu_format="fc32",
                channels=range(1),
            ),
        )
        self.usrp_source.set_samp_rate(sample_rate)
        self.usrp_source.set_center_freq(centre_freq,0)
        self.usrp_source.set_gain(gaindB,0)
        self.toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, fftsize)
        self.fftblock = fft.fft_vcc(fftsize,True,signal.get_window(('tukey',0.25),fftsize),True)
        self.spectroblock = spectrogram_img_c(fftsize,nrows,ncols,n_avgs,True)
        self.tcp_client = darkflow_tcp_client(self.yaml_config, addr, radio_metadata)

        # make flowgraph
        self.connect(self.usrp_source,self.toparallel)
        self.connect(self.toparallel,self.fftblock)
        self.connect(self.fftblock,self.spectroblock)
        self.msg_connect(self.spectroblock, "imgcv", self.tcp_client, "gray_img")

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Setup the files for training/testing')
    parser.add_argument('--config', type=str,
                        help='YAML file for config', required=False)
    parser.add_argument('--freq', type=float,
                        help='Rx frequency [Hz]', required=True)
    parser.add_argument('--host',type=str,default='127.0.0.1')
    args = parser.parse_args()

    addr = (args.host,9999)
    tb = DarkflowClientFlowGraph(args.config,addr,args.freq)
    tb.run()
