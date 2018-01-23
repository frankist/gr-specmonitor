#!/usr/bin/env python

import unittest
from gnuradio import gr, gr_unittest
# import specmonitor_swig as specmonitor
import specmonitor
import numpy as np
import matplotlib.pyplot as plt
import timeit

from labeling_framework.labeling_tools import preamble_utils
from labeling_framework.labeling_tools import random_sequence
from labeling_framework.utils import basic_algorithms as ba

def array_almost_equal(a,b,precision=5):
    return np.max(np.abs(a-b))<10**-precision

def generate_hier_preamble(pseq_len_list,pseq_lvl2_len,num_repeats=1):
    assert len(pseq_len_list)==2
    pseq_list = [random_sequence.zadoffchu_noDC_sequence(p,1,0) for p in pseq_len_list]
    lvl2_code = random_sequence.maximum_length_sequence(pseq_lvl2_len)
    lvl2_many = np.array([])
    for i in range(num_repeats):
        lvl2_many = np.append(lvl2_many,lvl2_code)
    pseq_list_coef = preamble_utils.set_schmidl_sequence(lvl2_many)
    pseq_list_coef = np.append(pseq_list_coef,1)
    pseq_len_seq = [0]*(pseq_lvl2_len*num_repeats+1)+[1]
    return specmonitor.PyPreambleParams(pseq_list,pseq_len_seq,pseq_list_coef)

def assert_consistency(tester,pydetec,detec,pypparams,pparams,x_with_hist):
    # initialization asserts
    x_hlen = pydetec.x_h.hist_len
    xdc_mavg_hlen = pydetec.xdc_mavg_h.hist_len
    xnodc_hlen = pydetec.xnodc_h.hist_len
    xschmidl_nodc_hlen = pydetec.xschmidl_nodc.hist_len
    xcorr_nodc_hlen = pydetec.xcorr_nodc.hist_len
    xcrossautocorr_nodc_hlen = pydetec.xcrossautocorr_nodc.hist_len
    tester.assertTrue(array_almost_equal(pypparams.pseq_list[0], pparams.subseq(0)))
    tester.assertTrue(array_almost_equal(pypparams.pseq_list_norm[0], pparams.subseq_norm(0)))
    tester.assertEqual(pydetec.__max_margin__,detec.N_margin)
    tester.assertEqual(pydetec.L0,detec.L0)
    tester.assertEqual(x_hlen,detec.d_x_hist_len)
    tester.assertEqual(xdc_mavg_hlen,detec.DC_moving_average_buffer_hist_len())
    tester.assertEqual(xnodc_hlen,detec.DC_cancelled_buffer_hist_len())
    tester.assertEqual(xschmidl_nodc_hlen,detec.SCox_noDC_hist_len())
    tester.assertEqual(xcorr_nodc_hlen,detec.crosscorrelation_noDC_hist_len())
    tester.assertEqual(xcrossautocorr_nodc_hlen,detec.test_statistics_hist_len())

    # assert buffers
    L0 = detec.L0
    x_h_len = len(x_with_hist)-x_hlen
    xdc_mavg_h = detec.DC_moving_average_buffer()
    pyxdc_mavg_h = pydetec.xdc_mavg_h[-xdc_mavg_hlen::]
    xnodc_h = detec.DC_cancelled_buffer()
    pyxnodc_h = pydetec.xnodc_h[-xnodc_hlen::]
    xschmidl_nodc_h = detec.SCox_noDC_buffer()
    pyxschmidl_nodc_h = pydetec.xschmidl_nodc[-xschmidl_nodc_hlen::]
    xschmidl_filt_nodc = detec.SCox_filt_buffer()
    pyxschmidl_filt_nodc = pydetec.xschmidl_filt_nodc
    xcorr_nodc_h = detec.crosscorrelation_noDC_buffer()
    pyxcorr_nodc_h = pydetec.xcorr_nodc[-xcorr_nodc_hlen::]
    xcrossautocorr_nodc_h = detec.test_statistics_buffer()
    pyxcrossautocorr_nodc_h = pydetec.xcrossautocorr_nodc[-xcrossautocorr_nodc_hlen::]
    tester.assertEqual(len(xdc_mavg_h),x_h_len+xdc_mavg_hlen)
    tester.assertTrue(array_almost_equal(x_with_hist,pydetec.x_h[-x_hlen::]))
    tester.assertTrue(array_almost_equal(xdc_mavg_h,pyxdc_mavg_h))
    tester.assertTrue(array_almost_equal(xnodc_h,pyxnodc_h))
    tester.assertTrue(array_almost_equal(xschmidl_nodc_h,pyxschmidl_nodc_h))
    tester.assertTrue(array_almost_equal(xschmidl_filt_nodc,pyxschmidl_filt_nodc,4))
    tester.assertTrue(array_almost_equal(xcorr_nodc_h,pyxcorr_nodc_h,4))
    tester.assertTrue(array_almost_equal(xcrossautocorr_nodc_h,pyxcrossautocorr_nodc_h,4))

    # assert moving average
    for i in range(x_h_len):
        movavg = np.sum(x_with_hist[i+x_hlen-L0+1:i+x_hlen+1])/float(L0)
        tester.assertAlmostEqual(movavg,xdc_mavg_h[i+xdc_mavg_hlen],5)

    # assert peaks are consistent
    peaks = preamble_utils.pmt_to_tracked_peaks(detec.pypeaks())
    pypeaks = pydetec.peaks
    tester.assertEqual(len(peaks),len(pypeaks))
    for i,p in enumerate(pypeaks):
        tester.assertTrue(p.is_almost_equal(peaks[i],5))
    # plt.plot(xcorr_nodc_h)
    # plt.plot(pyxcorr_nodc_h,'r:')
    # plt.show()

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
        sframer = preamble_utils.SignalFramer(pyfparams)
        L0 = pydetec.L0

        # generation of the C++ version
        pparams = generate_hier_preamble(pseq_len,pseq_lvl2_len,nrepeats0)
        fparams = specmonitor.PyFrameParams(pparams,guard_len,awgn_len,frame_period)
        detec = specmonitor.hier_preamble_detector(fparams,pseq_len[0]*8)

        # initialization asserts
        x_hlen = pydetec.x_h.hist_len
        xdc_mavg_hlen = pydetec.xdc_mavg_h.hist_len
        xnodc_hlen = pydetec.xnodc_h.hist_len
        xschmidl_nodc_hlen = pydetec.xschmidl_nodc.hist_len
        xcorr_nodc_hlen = pydetec.xcorr_nodc.hist_len
        xcrossautocorr_nodc_hlen = pydetec.xcrossautocorr_nodc.hist_len

        xlen = pyfparams.section_duration()+guard_len*2
        x = np.zeros(xlen,np.complex64)
        y,section_ranges = sframer.frame_signal(x,1)
        x = list([complex(yy) for yy in y])#list(range(10000))
        x_with_hist = list(np.zeros(x_hlen))+x

        detec.work(x_with_hist)
        pydetec.work(np.array(x))

        assert_consistency(self,pydetec,detec,pypparams,pparams,x_with_hist)

    def test_speed(self):
        guard_len=5
        awgn_len=200
        frame_period = 3000*2
        pseq_lvl2_len = len(random_sequence.maximum_length_sequence(13*8))#13*4
        pseq_len = [13,199]
        nrepeats0 = 1

        dc_offset = 2.0
        cfo = -0.45/pseq_len[0]

        pypparams = preamble_utils.generate_preamble_type2(pseq_len,
                                                           pseq_lvl2_len,
                                                           nrepeats0)
        pyfparams = preamble_utils.frame_params(pypparams,
                                                guard_len,awgn_len,
                                                frame_period)
        pparams = generate_hier_preamble(pseq_len,
                                         pseq_lvl2_len,nrepeats0)
        fparams = specmonitor.PyFrameParams(pparams,guard_len,
                                            awgn_len,
                                            frame_period)
        sframer = preamble_utils.SignalFramer(pyfparams)
        pydetec = preamble_utils.PreambleDetectorType2(pyfparams, pseq_len[0]*8,0.045,0.045)
        detec = preamble_utils.PyHierPreambleDetector(fparams,pseq_len[0]*8,0.045,0.045)

        x=np.zeros(int(pyfparams.frame_period*1.5),np.complex64)
        Nruns = 5
        for i in range(Nruns):
            y,section_ranges = sframer.frame_signal(x,1)
            x_with_hist = detec.x_hist_buffer + y.tolist()
            detec.work(y)
            pydetec.work(y)
            assert_consistency(self,pydetec,detec.detec,
                               pypparams,pparams,x_with_hist)

        # measure_speed(detec,pydetec,y)

def measure_speed(detec,pydetec,y):
    nruns = 100
    def call1():
        detec.work(y)
    def call2():
        pydetec.work(y)
    t1 = timeit.timeit(call1,number=nruns)
    t2 = timeit.timeit(call2,number=nruns)
    print 'total times:',t1,t2
    print 'C++ version is',t2/t1,'times faster than python'

if __name__ == '__main__':
    unittest.main()
