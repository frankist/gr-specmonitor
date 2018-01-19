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


#ifndef INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H
#define INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H

#include <specmonitor/api.h>
#include <complex>
#include "../../lib/utils/digital/volk_utils.h"
#include "../../lib/utils/digital/range_utils.h"

namespace gr {
namespace specmonitor {

  struct PreambleParams {
    
  };

  struct FrameParams {
    PreambleParams preamble_params;
  };

  class TrackedPeak {

  };

/*!
  * \brief <+description+>
  *
  */
class SPECMONITOR_API hier_preamble_detector
{
public:
  hier_preamble_detector(FrameParams fparams, int autocorr_margin = -1, float thres1 = 0.08, float thres2 = 0.04);
  // hier_preamble_detector() : d_fparams(), d_pparams(d_fparams.preamble_params) {}
  ~hier_preamble_detector();
  void work(const std::vector<std::complex<float> > x_h);
  void work(const std::complex<float>* x_h, int nsamples);
  void work(const utils::hist_array_view<const std::complex<float> >&x_h);

  // arguments
  FrameParams d_fparams;
  int d_autocorr_margin;
  float d_thres1;
  float d_thres2;

  // derived
  PreambleParams d_pparams;
  utils::array_view<std::complex<float> > d_lvl2_seq;
  std::vector<std::complex<float> > d_lvl2_seq_diff;
  utils::array_view<std::complex<float> > d_pseq0;
  int l0;
  int l1;
  int L0;
  int N_awgn;
  int N_margin;

  // internal
  long d_nread;
  std::vector<TrackedPeak> d_peaks;
  int d_margin;
  std::vector<int> d_delay;
  std::vector<int> d_delay2;
  std::vector<int> d_delay_cum;
  std::vector<int> d_delay2_cum;
  int d_hist_len2;
  int d_Ldiff;
  int d_x_hist_len;

 private:
  // internal buffers
  volk_utils::hist_volk_array<std::complex<float> > x_h;
  volk_utils::hist_volk_vector<std::complex<float> > xdc_mavg_h;
  volk_utils::hist_volk_array<std::complex<float> > xnodc_h;
  volk_utils::hist_volk_array<std::complex<float> > xschmidl_nodc_h;
  std::vector<std::complex<float> > xschmidl_filt_nodc;
  volk_utils::hist_volk_array<float> xcorr_nodc_h;
  std::vector<float> xcorr_filt_nodc;
  volk_utils::hist_volk_array<float> xcrosscautocorr_nodc_h;
  // SlidingWindowMaxHist* local_max_finder_h;

  // this is for debug mostly
 public:
  std::vector<std::complex<float> > DC_moving_average_buffer() const {
    return xdc_mavg_h.vector_clone();
  }
};

  // This is to call it from python
  hier_preamble_detector make_hier_preamble_detector_from_json(std::string js) {
    return hier_preamble_detector(FrameParams());
  }

} // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H */

