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
    'sample_rate':20.0e6
}

class DarkflowClientFlowGraph(gr.top_block):
    def __init__(self,yaml_config=''):
        super(DarkflowClientFlowGraph, self).__init__()

        # params
        self.yaml_config = yaml_config
        sample_rate = 20.0e6
        centre_freq = 2.3e9
        gaindB = 21#30
        fftsize = 104
        n_avgs = radio_metadata['n_avgs']
        ncols = radio_metadata['ncols']
        nrows = radio_metadata['nrows']
        addr = ('134.226.55.55',9999)

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
    args = parser.parse_args()

    tb = DarkflowClientFlowGraph(args.config)
    tb.run()
