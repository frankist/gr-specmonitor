#!/usr/bin/env python

import unittest
from gnuradio import gr, gr_unittest
# import specmonitor_swig as specmonitor
import specmonitor
import numpy as np
import matplotlib.pyplot as plt

from labeling_framework.labeling_tools import preamble_utils
from labeling_framework.labeling_tools import random_sequence
from labeling_framework.utils import basic_algorithms as ba

def array_almost_equal(a,b,precision=5):
    return np.max(np.abs(a-b))<10**-precision

class TestArrays(unittest.TestCase):
    def test_array_values(self):
        guard_len = 5
        awgn_len = 10
        frame_period = 5000
        nrepeats0 = 3
        pseq_len = [5,31]
        pseq_lvl2_len = len(random_sequence.maximum_length_sequence(3))#13*4

        # generation of python-version of preamble detector
        pypparams = preamble_utils.generate_preamble_type2(pseq_len,pseq_lvl2_len,
                                                           nrepeats0)
        pyfparams = preamble_utils.frame_params(pypparams,guard_len,
                                              awgn_len,frame_period)
        pydetec = preamble_utils.PreambleDetectorType2(pyfparams, pseq_len[0]*8)
        L0 = pydetec.L0
        print 'py params: l0:',pydetec.l0,'L0:',L0,',delay_cum:',pydetec.delay_cum

        # generation of the C++ version
        fparams = specmonitor.FrameParams()
        detec = specmonitor.hier_preamble_detector(fparams)

        # initialization asserts
        x_hlen = pydetec.x_h.hist_len
        self.assertEqual(pydetec.L0,detec.L0)
        self.assertEqual(x_hlen,detec.d_x_hist_len)

        x = list(range(1000))
        x_with_hist = list(np.zeros(x_hlen))+x

        detec.work(x_with_hist)
        pydetec.work(np.array(x))

        L0 = detec.L0
        x_h_len = len(x_with_hist)-x_hlen
        xdc_mavg_h = detec.DC_moving_average_buffer()
        xdc_mavg_hlen = pydetec.xdc_mavg_h.hist_len
        pyxdc_mavg_h = pydetec.xdc_mavg_h[-xdc_mavg_hlen::]
        print 'hist len',x_hlen,xdc_mavg_hlen

        # assert x input
        self.assertTrue(array_almost_equal(x_with_hist,pydetec.x_h[-x_hlen::]))
        # assert moving average
        self.assertEqual(len(xdc_mavg_h),x_h_len+xdc_mavg_hlen)
        for i in range(x_h_len):
            movavg = np.sum(x_with_hist[i+x_hlen-L0+1:i+x_hlen+1])/float(L0)
            self.assertAlmostEqual(movavg,xdc_mavg_h[i+xdc_mavg_hlen],5)
        self.assertTrue(array_almost_equal(xdc_mavg_h,pyxdc_mavg_h[0::]))
        # assert dc computation
        # print 'x_with_hist:',np.array(x_with_hist)[x_hlen::][0:10]
        # print 'xdc_mavg:',np.array(xdc_mavg_h[xdc_mavg_hlen::][0:10])
        # print 'pyxdc_mavg:',np.array(pyxdc_mavg_h[xdc_mavg_hlen::][0:10])

        plt.plot(x[x_hlen::])
        plt.plot(xdc_mavg_h[xdc_mavg_hlen::],'r:')
        plt.plot(pyxdc_mavg_h[xdc_mavg_hlen::],'x')
        # plt.plot(ba.moving_average_with_hist(pydetec.x_h,L0),'x')
        plt.show()


if __name__ == '__main__':
    unittest.main()
