""" Testing GDB, yay """

import os
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
import specmonitor as specmonitor
#import specmonitor_swig as specmonitor
import numpy as np

class CreateRadio(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self,name="Corr Norm")
        sample_rate = 1e6
        total_samples = 10000
        preamble_seq = np.array([1,1,-1,1])
        preamble_seq /= len(preamble_seq)

        self.vector_source = blocks.vector_source_c(preamble_seq*4, True)
        self.head = blocks.head(gr.sizeof_gr_complex, total_samples)
        self.corr_est = specmonitor.corr_est_norm_cc(preamble_seq, 1, 0)
        self.tag_db = blocks.tag_debug(gr.sizeof_gr_complex, "tag debugger")
        self.dst = blocks.vector_sink_c()

        self.connect(self.vector_source,self.head)
        self.connect(self.head,self.corr_est)
        self.connect(self.corr_est,self.tag_db)
        self.connect(self.corr_est,self.dst)


def main():
    """ go, go, go """
    top_block = CreateRadio()
    top_block.run()

if __name__ == "__main__":
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    raw_input ('Press Enter to continue: ')
    main()
