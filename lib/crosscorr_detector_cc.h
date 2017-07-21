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

#include <gnuradio/filter/fft_filter.h>
#include "utils/digital/moving_average.h"
#include <volk/volk.h>
#include "utils/math/operation.h"
#include "utils/math/transform.h"
#include <numeric>

#ifndef _CROSSCORR_DETECTOR_CC_H_
#define _CROSSCORR_DETECTOR_CC_H_

namespace gr {
  namespace specmonitor {
    class interleaved_moving_average {
    public:
      int d_idx;
      int d_len;
      std::vector<utils::moving_average<float> > d_mavg_vec;

      interleaved_moving_average(int len,int mavg_size);
      void execute(float* x, float* y, int n);
    };

    class detection_instance {
    public:
      long idx;
      float corr_val;
      utils::moving_average<gr_complex> schmidl_vals;
      bool valid;
    detection_instance(int siz) : schmidl_vals(siz), valid(false) {}
      static bool idx_compare(const detection_instance& a, const detection_instance& b) {return a.idx < b.idx;}
    };

    class crosscorr_detector_cc {
    public:
      std::vector<gr_complex> d_pseq;
      int d_n_repeats;
      float d_thres;
      size_t d_seq_len;

      gr_complex* d_corr;
      float *d_corr_mag;
      float *d_smooth_corr;
      interleaved_moving_average d_interleaved_mavg;
      gr::filter::kernel::fft_filter_ccc* d_filter;
      std::vector<detection_instance> peaks;

      crosscorr_detector_cc(const std::vector<gr_complex>& pseq, int n_repeats, int nitems, float thres);

      ~crosscorr_detector_cc();

      void work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn);
    };

    interleaved_moving_average::interleaved_moving_average(int len,int mavg_size) :
      d_idx(0), d_len(len), d_mavg_vec(len,mavg_size) {
    }

    void interleaved_moving_average::execute(float* x, float*y, int n) {
      for(int i = 0; i < n; ++i) {
        y[i] = d_mavg_vec[d_idx].execute(x[i]);
        d_idx = (d_idx+1)%d_len;
      }
    }

    crosscorr_detector_cc::crosscorr_detector_cc(const std::vector<gr_complex>& pseq,
                                                 int n_repeats, int nitems, float thres) :
      d_pseq(pseq), d_n_repeats(n_repeats), d_thres(thres), d_seq_len(pseq.size()),
      d_interleaved_mavg(pseq.size(),n_repeats) {
      d_corr = (gr_complex *) volk_malloc(sizeof(gr_complex)*nitems, volk_get_alignment());
      d_corr_mag = (float *) volk_malloc(sizeof(float)*nitems, volk_get_alignment());
      d_smooth_corr = (float *) volk_malloc(sizeof(float)*nitems, volk_get_alignment());
      float pwr = std::accumulate(&d_pseq[0], &d_pseq[d_pseq.size()], 0.0, utils::OpAccNorm);//utils::mean_mag2(&d_pseq[0], d_pseq.size());
      utils::scale(&d_pseq[0], 1/sqrt(pwr), d_pseq.size());
      std::vector<gr_complex> pseq_filt = d_pseq;
      utils::conj(&pseq_filt[0], pseq_filt.size());
      std::reverse(pseq_filt.begin(), pseq_filt.end());
      d_filter = new gr::filter::kernel::fft_filter_ccc(1, pseq_filt);
    }

    crosscorr_detector_cc::~crosscorr_detector_cc() {
      volk_free(d_corr);
      volk_free(d_corr_mag);
      volk_free(d_smooth_corr);
      delete d_filter;
    }

    void crosscorr_detector_cc::work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn) {
      long d_corr_toffset = n_read + hist_len - d_seq_len + 1;
      // We first calculate the cross-correlation and mag2 it
      d_filter->filter(noutput_items, &in[hist_len], d_corr);
      volk_32fc_magnitude_squared_32f(&d_corr_mag[0], d_corr, noutput_items);

      // make an interleaved moving average as we know the peaks are at a similar distance
      d_interleaved_mavg.execute(&d_corr_mag[0], &d_smooth_corr[0], noutput_items);

      // If we find a peak in the smoothed crosscorr, we may have found the preamble
      unsigned short max_i;
      volk_32f_index_max_16u(&max_i, d_smooth_corr, noutput_items);
      if(d_smooth_corr[max_i] > d_thres*awgn) { // d_thres*d_awgn
        long sample_idx = d_corr_toffset + max_i;
        int p_;
        for(p_ = 0; p_ < peaks.size(); ++p_) {
          if(peaks[p_].idx+d_seq_len == sample_idx) {
            if(peaks[p_].corr_val < d_smooth_corr[max_i]) {
              peaks[p_].idx = sample_idx;
              peaks[p_].corr_val = d_smooth_corr[max_i];
              std::cout << "DEBUG: Updating peak. New peak position: " << sample_idx << std::endl;
              std::sort(peaks.begin(),peaks.end(),detection_instance::idx_compare);
            }
            else {
              peaks[p_].valid = true;
              std::cout << "A peak solution was found at " << peaks[p_].idx
                        << ": " << peaks[p_].corr_val << std::endl;
            }
            break;
          }
        }
        if(p_ == peaks.size()) { // this is a new peak hypothesis
          detection_instance new_peak(d_n_repeats-1);
          // go back several positions to start computing the autocorrelation
          int past_idx = std::max((int)max_i - (int)(d_n_repeats*d_seq_len),0);// FIXME: do i need to check if >0 ?
          for(int k = 0; k < d_n_repeats-1; ++k) {
            int idx = past_idx + k*d_seq_len, idx2 = idx + d_seq_len;
            gr_complex res;
            volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in[idx], &in[idx2], d_seq_len);
            new_peak.schmidl_vals.execute(res);
          }
          new_peak.idx = sample_idx;
          new_peak.corr_val = d_smooth_corr[max_i];
          peaks.push_back(new_peak);
          std::cout << "A peak candidate was found at " << new_peak.idx
                    << ": " << new_peak.corr_val << std::endl;
        }
        else if(peaks[p_].valid==false) { // the peak was updated. Update also its schmidl&cox phase
          int past_idx = std::max((int)max_i-(int)d_seq_len,0);
          gr_complex res;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res,&in[past_idx],&in[max_i], d_seq_len);
          peaks[p_].schmidl_vals.execute(res);
        }
      }

      // check for peaks that are maximal
      for(int p_ = 0; p_ < peaks.size(); ++p_)
        if(peaks[p_].idx + d_seq_len <  d_corr_toffset + noutput_items) {
          peaks[p_].valid = true;
          std::cout << "A peak solution was found at " << peaks[p_].idx
                    << ": " << peaks[p_].corr_val << std::endl;
        }
    }
  }
}

#endif
