/* -*- c++ -*- */
/* 
 * Copyright 2018 <+YOU OR YOUR COMPANY+>.
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <iostream>
#include <gnuradio/io_signature.h>
#include <specmonitor/hier_preamble_detector.h>
#include "utils/digital/hist_algorithm.h"
#include "utils/prints/print_ranges.h"

namespace gr {
namespace specmonitor {

  hier_preamble_detector::hier_preamble_detector(FrameParams fparams, int autocorr_margin, float thres1, float thres2) :
    d_fparams(fparams),
    d_autocorr_margin(autocorr_margin),
    d_thres1(thres1),
    d_thres2(thres2),
    d_pparams(d_fparams.preamble_params)
{
  // vector<std::complex<float> > &v = d_pparams.pseq_list_coef;
  // d_lvl2_seq.reset(v.begin(), v.end());
//   // d_pseq0.reset(d_pparams.pseq_list_norm[0]);
//   // L = d_pparams.length();
  // l0 = d_pseq0.size();
//   // l1 = d_pparams.pseq_list_norm[1].size();
  L0 = 50;//l0*d_lvl2_seq.size();
//   // d_lvl2_seq_diff = get_schmidl_sequence(&d_lvl2_seq[0],&d_lvl2_seq.endref());
//   // N_awgn = fparams.awgn_gap_size();
  N_margin = (autocorr_margin<0) ? L0 : autocorr_margin;

  d_nread = 0;
  d_margin = 4;
//   // d_hist_len = N_awgn + L;
  // d_delay.push_back(L0-1);
  // d_delay.push_back(l0*2-1);
  // d_delay.push_back(d_lvl2_seq_diff.size()*l0-1);
  // d_delay2.push_back(d_delay[0]);
  // d_delay2.push_back(l0-1);
  // d_delay2.push_back(L0-1);
  // d_delay_cum = cumsum(d_delay);
  d_delay_cum.resize(3);
  d_delay_cum[2] = 102;
//   // d_delay2_cum = cumsum(d_delay2);
//   // d_hist_len2 = d_delay2_cum[2]+L+N_awgn+2*N_margin;
//   // d_Ldiff = std::max(d_l1-N_margin,0);

  // NOTE: we look back in time by self.delay_cum[2] to find peaks
  d_x_hist_len = 102;
//   // // x_h.resize(std::max(d_delay_cum[0],L0));
  xdc_mavg_h.reserve(52, 1000);//d_delay_cum[2]-L0); // FIXME: set the size. not just the hist
  xdc_mavg_h.fill_history(std::complex<float>(0,0));
//   // xnodc_h.resize(L0+d_delay_cum[0]+d_margin+l1);
//   // xschmidl_nodc_h.resize(L0);
//   // // xschmidl_filt_nodc.resize();
//   // xcorr_nodc_h.resize(L0);
//   // // xcorr_filt_nodc;
//   // xcrossautocorr_nodc_h.resize(N_margin+d_Ldiff);
//   // local_max_finder_h = new SlidingWindowMaxHist(N_margin);
}

hier_preamble_detector::~hier_preamble_detector()
{
  // delete local_max_finder_h;
}


  void hier_preamble_detector::work(const std::vector<std::complex<float> > x_h) {
    assert(x_h.size()>d_x_hist_len);
    utils::hist_array_view<const std::complex<float> > x2_h(&x_h[0],d_x_hist_len,x_h.size()-d_x_hist_len);
    work(x2_h);
  }

  void hier_preamble_detector::work(const std::complex<float>* x_h, int nsamples) {
    assert(nsamples>d_x_hist_len);
    utils::hist_array_view<const std::complex<float> > x2_h(&x_h[0],d_x_hist_len,nsamples-d_x_hist_len);
    work(x2_h);
  }

  void hier_preamble_detector::work(const utils::hist_array_view<const std::complex<float> >& x_h) {
    xdc_mavg_h.flush(x_h.size());
    utils::moving_average_hist(&xdc_mavg_h[0],&x_h[0],&x_h[x_h.size()],L0);
    // for(int i = 0; i < xdc_mavg_h.size(); ++i)
    //   xnodc_h[i] = x_h[-L0+1+i]-xdc_mavg_h[i];
    // compute_schmidl_cox_hist(&xschmidl_nodc_h[0],&xnodc_h[0],&xnodc_h[xnodc_h.size()],l0);
    // for(int i = 0; i < xschmidl_nodc_h.size(); ++i)
    //   xschmidl_nodc_h[i] /= (float)l0;
    // if(d_nread<d_delay_cum[1])
    //   std::fill(&xschmidl_nodc_h[0],&xschmidl_nodc_h[std::min(d_delay_cum[1]-d_nread, xschmidl_nodc_h.size())]);
    // interleaved_crosscorrelate_hist(&xschmidl_filt_nodc[0],&xschmidl_nodc_h[0],&xschmidl_nodc_h[xschmidl_nodc_h.size()],d_lvl2_seq_diff,l0);
    // for(int i = 0; i < xschmidl_filt_nodc_h.size(); ++i)
    //   xschmidl_filt_nodc[i] /= d_lvl2_seq_diff.size();
    // correlate_hist(&tmp[0], &xnodc_h[0], &xnodc_h[xnodc_h.size()], d_pseq0);
    // for(int i = 0; i < xcorr_nodc_h.size(); ++i)
    //   xcorr_nodc_h[i] = std::norm(tmp[i]/l0);
    // xcorr_filt_nodc = interleaved_sum_hist(&xcorr_nodc_h[0], &xcorr_nodc_h[xcorr_nodc_h.size()], lvl2_len, l0);
    // for(int i = 0; i < xcorr_nodc_h.size(); ++i)
    //   xcorr_filt_nodc[i] /= d_lvl2_seq.size();
    // for(int i = 0; i < xcorr_filt_nodc.size(); ++i)
    //   xcrossautocorr_nodc[i] = std::abs(xschmidl_filt_nodc)*xcorr_filt_nodc;

    // float& xfinaltest = xcrossautocorr_nodc[-d_Ldiff]; // should have size==x.size()
    // std::vector<int> local_peaks = local_max_finder_h.work(xfinaltest,xcrossautocorr_nodc.size());
    // for(int i = 0; i < local_peaks.size(); ++i) {
    //   local_peaks[i] -= d_Ldiff;
    // }
  }

} /* namespace specmonitor */
} /* namespace gr */

