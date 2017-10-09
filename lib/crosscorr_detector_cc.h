/* -*- c++ -*- */
/* 
 * Copyright 2017 Francisco Paisana.
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

#include <gnuradio/filter/fir_filter_with_buffer.h>
#include "utils/digital/moving_average.h"
#include <volk/volk.h>
#include "utils/math/transform.h"
#include <numeric>
#include "utils/serialization/rapidjson/stringbuffer.h"
#include "utils/serialization/rapidjson/prettywriter.h"
#include "utils/serialization/rapidjson/document.h"
#include "utils/prints/print_ranges.h"
#include "utils/digital/volk_utils.h"
#include "utils/digital/range_utils.h"
#include "frame_params.h"
#include "tracked_peak.h"
#include "utils/general/tictoc.h"
#include "modules/interleaved_filtering.h"

#ifndef _CROSSCORR_DETECTOR_CC_H_
#define _CROSSCORR_DETECTOR_CC_H_

namespace gr {
  namespace specmonitor {

    gr_complex autocorrelate(const utils::hist_array_view<const gr_complex>& in_h,
                             int start_idx, int delay, int n_samples) {
      gr_complex res;
      volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in_h[start_idx], &in_h[start_idx+delay], n_samples);
      return res;
    }

    class crosscorr_detector_cc {
    public:
      const frame_params* d_frame;
      float d_thres;

      // derived
      int d_len0;
      int d_len0_tot;

      // internal
      volk_utils::volk_array<gr_complex> d_corr;
      volk_utils::volk_array<float> d_corr_mag;
      volk_utils::hist_volk_array<float> d_smooth_corr_h;
      interleaved_moving_average_fff d_interleaved_mavg;
      gr::filter::kernel::fir_filter_with_buffer_ccc* d_filter;
      int d_max_margin;
      std::vector<preamble_peak> peaks;

      volk_utils::hist_volk_array<float> d_xmag2_h;
      // volk_utils::hist_volk_array<float> d_xautocorr_h;

      // internal state
      int d_kk_start;
      int d_peakno;

      // debug
      std::vector<TicToc> tictoc_vec;

      crosscorr_detector_cc(const frame_params* f_params, int nitems, float thres, float awgn_guess = 1);

      ~crosscorr_detector_cc();

      void compute_autocorr(preamble_peak& new_peak, const utils::hist_array_view<const gr_complex>& in_h, int max_i);
      bool check_if_max_within_margin(int &midx, gr_complex &autocorr_res,
                                      const utils::hist_array_view<const gr_complex>& in_h,
                                      float *xcorr_ptr, int tidx);
      void work(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int hist_len, int n_read, float awgn);
      std::string peaks_to_json();
      bool is_existing_peak(long new_idx);
    };

    crosscorr_detector_cc::crosscorr_detector_cc(const frame_params* f_params,
                                                 int nitems, float thres, float awgn_guess) :
      d_frame(f_params), d_thres(thres),
      d_len0(f_params->len[0]),
      d_len0_tot(f_params->len[0]*f_params->n_repeats[0]),
      d_interleaved_mavg(f_params->len[0],f_params->n_repeats[0]),
      d_kk_start(0),
      d_peakno(0) {
      std::vector<float> v(d_len0_tot,awgn_guess);
      d_interleaved_mavg.execute(&v[0],v.size());

      d_max_margin = d_len0_tot - d_len0 + 1; // peaks in crosscorr0 have to be maximum within a window of this size

      // this will compute the crosscorr with peak0
      d_corr.resize(nitems);
      d_corr_mag.resize(nitems);
      d_smooth_corr_h.resize(d_max_margin, nitems);
      std::fill(&d_smooth_corr_h[-d_max_margin],&d_smooth_corr_h[0], 0);

      // Create a Filter. First normalize the taps, then reverse conjugate them.
      std::vector<gr_complex> pseq_filt(&d_frame->pseq_vec[0][0], &d_frame->pseq_vec[0][d_len0]);
      utils::normalize(&pseq_filt[0], pseq_filt.size());
      utils::conj(&pseq_filt[0], pseq_filt.size());
      std::reverse(pseq_filt.begin(), pseq_filt.end());
      d_filter = new gr::filter::kernel::fir_filter_with_buffer_ccc(pseq_filt);

      // We keep the mag2 of the received signal to compute the energy and AWGN
      d_xmag2_h.resize(d_max_margin + d_len0_tot + d_frame->awgn_len, nitems);
      std::fill(&d_xmag2_h[-d_xmag2_h.hist_len()],&d_xmag2_h[0], awgn_guess);

      // d_xautocorr_h.resize(d_max_margin + d_len0_tot, nitems);
      // std::fill(&d_xautocorr_h[-d_xautocorr_h.hist_len()], &d_xautocorr_h[0], awgn_guess);
    }

    crosscorr_detector_cc::~crosscorr_detector_cc() {
      delete d_filter;
    }

    void crosscorr_detector_cc::compute_autocorr(preamble_peak& new_peak,
                                                 const utils::hist_array_view<const gr_complex>& in_h,
                                                 int max_i) {
      // assert(1-d_len0_tot >= 0);
      // FIXME: Check if this past_idx equation is correct
      int past_idx = 1 + max_i - d_len0_tot; // look back to the beginning of the preamble
      for(int k = 0; k < d_frame->n_repeats[0]-1; ++k) {
        int idx = past_idx + k*d_len0, idx2 = idx + d_len0;
        gr_complex res;
        volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in_h[idx], &in_h[idx2], d_len0);
        res /= d_len0;
        // new_peak.schmidl_vals.execute(res);
        // std::cout << "max_i:" << max_i << ",idx:" << idx << ",in[idx]:" << in[idx] << std::endl;
      }
    }

    bool crosscorr_detector_cc::check_if_max_within_margin(int &midx, gr_complex &autocorr_res,
                                    const utils::hist_array_view<const gr_complex>& in_h,
                                    float *xcorr_ptr, int tidx) {
      // find maximum to the right within d_max_margin
      unsigned short umidx;
      volk_32f_index_max_16u(&umidx, xcorr_ptr + 1, d_max_margin-1);
      midx = (int)umidx+1;

      gr_complex res = autocorrelate(in_h, tidx+1-d_len0_tot, d_len0, d_len0_tot-d_len0);
      bool test1 = xcorr_ptr[0] < xcorr_ptr[midx];
      bool test2 = abs(xcorr_ptr[0]-xcorr_ptr[midx])/xcorr_ptr[0] < 0.01;
      if(test2) {
        gr_complex res2 = autocorrelate(in_h, tidx+1-d_len0_tot+midx, d_len0, d_len0_tot-d_len0);
        if(abs(res2) > abs(res)) {
          autocorr_res = res2;
          return false;
        }
        else {
          autocorr_res = res;
          return true;
        }
      }
      else if(test1) {
        gr_complex res2 = autocorrelate(in_h, tidx+1-d_len0_tot+midx, d_len0, d_len0_tot-d_len0);
        autocorr_res = res2;
        return false;
      }

      autocorr_res = res;
      return true;
    }

    void crosscorr_detector_cc::work(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int hist_len, int n_read, float awgn) {
      peaks.clear();

      int n_repeats0 = d_frame->n_repeats[0];
      long d_corr_toffset = n_read - d_len0 + 1 - d_max_margin;// points to absolute tstamp of beginning of filter

      // We first calculate the cross-correlation and mag2 it
      d_filter->filterN(&d_corr[0], &in_h[0], noutput_items);
      volk_32fc_magnitude_squared_32f(&d_corr_mag[0], &d_corr[0], noutput_items);

      // make an interleaved moving average as we know the peaks are at a similar distance
      d_interleaved_mavg.execute(&d_corr_mag[0], &d_smooth_corr_h[0], noutput_items);

      // Find the magnitude squared of the original signal and average it
      volk_32fc_magnitude_squared_32f(&d_xmag2_h[0], &in_h[0], noutput_items);
      // NOTE: we divide by a delayed power of the signal. We expect that the samples before the preamble are
      // just noise/uncontaminated
      std::cout << "DEBUG: window: [" << d_corr_toffset << "," << d_corr_toffset+noutput_items << "], noutput_items: " << noutput_items << std::endl;

      int kk, kkprev = d_kk_start-2;
      float mag2_sum;
      for(kk = d_kk_start; kk < noutput_items; ++kk) {
        int klast = kkprev;
        kkprev = kk;

        int tt = kk - d_max_margin;
        float *xcorr_ptr = &d_smooth_corr_h[tt]; // this points to the d_smooth_corr point under analysis. (It can be in history)

        int midx;
        gr_complex res;
        bool test = check_if_max_within_margin(midx,res,in_h,xcorr_ptr,tt);
        if(test==false) {
          kk = kk + midx - 1; // kk is going to be incremented at the for(;;), so we subtract by zero
          continue;
        }

        float *xmag2_ptr = &d_xmag2_h[tt-d_len0_tot+1];
        float *awgn_ptr = &d_xmag2_h[tt-d_len0_tot-d_frame->awgn_len+1];

        float peak_corr = xcorr_ptr[0] / d_len0;  // This is the mean power of the corr smoothed across repeats.
        long peak_idx = d_corr_toffset + kk;
        if(klast + 1 != kk || kk%100==0)
          mag2_sum = std::accumulate(xmag2_ptr,xmag2_ptr + d_len0_tot,0.0);
        else
          mag2_sum += xmag2_ptr[d_len0_tot-1] - xmag2_ptr[-1];
        float peak_mag2 = mag2_sum / d_len0_tot;
        // const gr_complex *pin = &in_h[kk-d_smooth_corr_h.hist_len+1-d_len0_tot];
        // volk_32fc_x2_conjugate_dot_prod_32fc(&res, pin, pin, d_len0_tot);
        // float peak_mag2_3 = std::abs(res)/d_len0_tot;

        if(peak_corr > d_thres*peak_mag2) { //*awgn_estim
          // NOTE: i don't use AWGN for normalization, as it would make my detector sensitive to the energy of the sent signal
          float awgn_estim = std::accumulate(awgn_ptr,awgn_ptr + d_frame->awgn_len,0.0)/d_frame->awgn_len;
          gr_complex res2 = (std::abs(res)/(d_len0_tot-d_len0)) * std::exp(gr_complex(0,std::arg(res)/d_len0));
          preamble_peak p(peak_idx-d_len0_tot+d_len0, peak_corr, peak_mag2, res2, awgn_estim);
          peaks.push_back(p);
          std::cout << "STATUS: Crosscorr Peak0 detected at " << peak_idx << ": " << println(p) << std::endl;

          kk += d_max_margin + d_len0 + d_frame->len[1];  // skip the margin examined, plus the pseq1, as the crosscorr(pseq0,pseq1) may not be zero, and the detector may get a false positive
        }
      }

      // NOTE: if there was a hop bigger than the block, we do not continue from position kk=0 in the next call
      d_kk_start = kk-noutput_items;

      d_smooth_corr_h.advance(noutput_items);
      d_xmag2_h.advance(noutput_items);

      double ratio = std::accumulate(&tvec[0],&tvec[2],0.0);
    }

    bool crosscorr_detector_cc::is_existing_peak(long new_idx) {
      for(int p_ = 0; p_ < peaks.size(); ++p_) {
        long rots = round((new_idx - peaks[p_].tidx)/(double)d_frame->frame_period)*d_frame->frame_period;
        int diff = abs(new_idx - (peaks[p_].tidx + rots));
        if(diff < 5) {
          std::cout << "DEBUG: Peak at " << new_idx
                    << " is an already existing one. Going to ignore..." << std::endl;
          return true;
        }
      }
      return false;
    }

    std::string crosscorr_detector_cc::peaks_to_json() {
      using namespace rapidjson;

      rapidjson::StringBuffer s;
      Document d;
      rapidjson::PrettyWriter<rapidjson::StringBuffer> w(s);
      std::vector<std::string> peak_strs(peaks.size());

      w.StartArray();
      for(std::vector<preamble_peak>::iterator it = peaks.begin(); it != peaks.end(); ++it) {
        w.StartObject();
        w.String("idx");
        w.Int(it->tidx);
        w.String("corr_val");
        w.Double(it->corr_mag);
        w.String("peak_mag2");
        w.Double(it->preamble_mag2);
        w.String("schmidl_mean");
        w.String(print_complex(it->autocorr_val).c_str());
        w.EndObject();
      }
      w.EndArray();

      std::string st = s.GetString();
      d.Parse(st.c_str());
      return st;
    }
  }
}

#endif
