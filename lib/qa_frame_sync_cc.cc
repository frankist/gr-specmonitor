/* -*- c++ -*- */
/* 
 * Copyright 2017 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */


#include <gnuradio/attributes.h>
#include <cppunit/TestAssert.h>
#include "qa_frame_sync_cc.h"
#include <specmonitor/frame_sync_cc.h>
#include "utils/digital/moving_average.h"
#include "utils/prints/print_ranges.h"
#include "utils/digital/channel.h"
#include "utils/digital/zadoffchu.h"
// #include <volk/volk.h>
// #include "crosscorr_detector_cc.h"
#include <fstream>

namespace gr {
  namespace specmonitor {

    void qa_frame_sync_cc::t1() {
      // Test Moving Average
      int size = 5;
      int val_size = 10;
      utils::moving_average<float> mavg(size);
      utils::moving_average<float> mavg2(size);
      float values[val_size] = {0,1,2,3,4,5,6,7,8,9};
      float res[val_size], res2[val_size];
      float expected_results[val_size] = {0,0.2,0.6,1.2,2.0,3.0,4.0,5.0,6.0,7.0};
      float diff = 0, diff2 = 0;

      mavg.execute(&values[0], &res[0], val_size);
      for(int i = 0; i < val_size; ++i) {
        res2[i] = mavg2.execute(values[i]);
        diff += std::abs(res[i]-res2[i]);
        diff2 += std::abs(res[i]-expected_results[i]);
      }

      CPPUNIT_ASSERT(diff < 0.001);
      CPPUNIT_ASSERT(diff2 < 0.001);
      // std::cout << container::print(&res[0], &res[val_size]);
    }

    void qa_frame_sync_cc::t2() {
      // Test the cross correlator peak detector
      int seq_len = 11, n_repeats = 4;
      std::vector<gr_complex> pseq(seq_len);
      utils::generate_zc_sequence(&pseq[0], 1, 0, seq_len);
      int N = 1000, hist_len = 3*seq_len, toffset = 100;
      float cfo = 0.4/seq_len;
      std::vector<gr_complex> x(N), x_cfo(N);
      for(int r = 0; r < n_repeats; r++) {
        for(int i = 0; i < seq_len; ++i) {
          x[toffset+hist_len+i+r*seq_len] = pseq[i];
        }
      }
      utils::frequency_shift(&x_cfo[0], &x[0], cfo, N);
      int expected_peak_idxs[1] = {hist_len+toffset};

      // float *var;
      // var = (float*) volk_malloc(sizeof(float)*1, volk_get_alignment());

      // ::gr::specmonitor::crosscorr_detector_cc detector(pseq, n_repeats, 1024*12, 0.8);
      // ::gr::specmonitor::crosscorr_detector_cc detector2(pseq, n_repeats, 1024*12, 0.8);

      // detector.work(&x[0], N, 3*seq_len, 0, 1);
      // detector2.work(&x_cfo[0], N, 3*seq_len, 0, 1);

      // if(1) {
      //   std::ofstream fp("/home/xico/tmp/test_python.py");
      //   if(!fp.is_open()) {
      //     std::cout << "ERROR: Couldn't open file" << std::endl;
      //     exit(1);
      //   }
      //   fp << "#!/usr/bin/env python\n"
      //      << "import numpy as np\n"
      //      << "import matplotlib.pyplot as plt\n\n"
      //      << "if __name__ == '__main__':\n";
      //   // fp << "    in = " << range::print(x) << std::endl;
      //   fp << "    a = " << container::print(&detector.d_corr_mag[0],&detector.d_corr_mag[N]) << "\n";
      //   fp << "plt.plot(a);\n"
      //      << "plt.show();\n";
      // }

      // // std::filestream
      // // std::cout << container::print(&detector.d_corr_mag[0],&detector.d_corr_mag[N]) << std::endl;
      // for(int i = 0; i < detector.peaks.size(); ++i)
      //   std::cout << detector.peaks[i].idx << ":" << detector.peaks[i].corr_val << std::endl;
    }
  } /* namespace specmonitor */
} /* namespace gr */

