#!/usr/bin/env python

from gnuradio import gr, gr_unittest
from gnuradio import blocks
from darkflow_tcp_client import darkflow_tcp_client

class qa_darkflow_tcp_client (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001_t(self):
        # fftsize = 104
        # n_samples = fftsize*104*50
        # vector_source = blocks.vector_source_c(xtuple, True)
        # head = blocks.head(gr.sizeof_gr_complex, n_samples)
        # toparallel = blocks.stream_to_vector(gr.sizeof_gr_complex, fftsize)
        # fftblock = fft.fft_vcc(64,True,signal.get_window(('tukey',0.25),104),True)
        # spectroblock = specmonitor.spectrogram_img_c(104, 104, 104, 10, True)
        # tcp_client = darkflow_tcp_client(yaml_file, 104)

        # set up fg
        self.tb.run()
        # check data


if __name__ == '__main__':
    gr_unittest.run(qa_darkflow_tcp_client, "qa_darkflow_tcp_client.xml")
