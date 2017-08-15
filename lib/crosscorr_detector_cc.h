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
#include "utils/math/transform.h"
#include <numeric>
#include "utils/serialization/rapidjson/stringbuffer.h"
#include "utils/serialization/rapidjson/prettywriter.h"
#include "utils/serialization/rapidjson/document.h"
#include "utils/prints/print_ranges.h"
#include "utils/digital/volk_utils.h"

#ifndef _CROSSCORR_DETECTOR_CC_H_
#define _CROSSCORR_DETECTOR_CC_H_

namespace gr {
  namespace specmonitor {
    class frame_params {
    public:
      std::vector<gr_complex*> pseq_vec;
      std::vector<size_t> len;
      std::vector<int> n_repeats;
      long frame_period;
      int awgn_len;
      frame_params(const std::vector<std::vector<gr_complex> >& p_vec, const std::vector<int>& n_r,
                   long f_period, int awgn_l) :
        pseq_vec(p_vec.size()), len(p_vec.size()),
        n_repeats(p_vec.size()), frame_period(f_period), awgn_len(awgn_l) {
        assert(pseq_vec.size()==n_r.size());
        for(int i = 0; i < p_vec.size(); ++i) {
          len[i] = p_vec[i].size();
          pseq_vec[i] = (gr_complex*) volk_malloc(sizeof(gr_complex)*len[i], volk_get_alignment());
          std::copy(&p_vec[i][0], &p_vec[i][len[i]], &pseq_vec[i][0]);
          utils::normalize(&pseq_vec[i][0], len[i]);
        }
        n_repeats = n_r;
      }
      ~frame_params() {
        for(int i = 0; i < pseq_vec.size(); ++i) {
          volk_free(pseq_vec[i]);
        }
      }
    };

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
      float peak_mag2;
      float awgn_estim;
      utils::moving_average<gr_complex> schmidl_vals;
      bool valid;
      bool tracked;
      detection_instance(int siz) : schmidl_vals(siz), valid(false), tracked(false) {}
      static bool idx_compare(const detection_instance& a, const detection_instance& b) {return a.idx < b.idx;}
      static bool is_valid(const detection_instance& a) {return a.valid;}
    };

    class crosscorr_detector_cc {
    public:
      const frame_params* d_frame;
      float d_thres;

      gr_complex* d_corr;
      float *d_corr_mag;
      float *d_smooth_corr;
      float *d_in_mag2;
      float *d_mavg_mag2;
      interleaved_moving_average d_interleaved_mavg;
      gr::filter::kernel::fft_filter_ccc* d_filter;
      // gr::filter::kernel::fft_filter_fff* d_filter2;
      volk_utils::moving_average<float> *awgn_mavg;
      std::vector<detection_instance> peaks;

      crosscorr_detector_cc(const frame_params* f_params, int nitems, float thres);

      ~crosscorr_detector_cc();

      void work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn);
      std::string peaks_to_json();
      bool is_existing_peak(long new_idx);
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

    crosscorr_detector_cc::crosscorr_detector_cc(const frame_params* f_params,
                                                 int nitems, float thres) :
      d_frame(f_params), d_thres(thres),
      d_interleaved_mavg(f_params->len[0],f_params->n_repeats[0]) {

      d_corr = (gr_complex *) volk_malloc(sizeof(gr_complex)*nitems, volk_get_alignment());
      d_corr_mag = (float *) volk_malloc(sizeof(float)*nitems, volk_get_alignment());
      d_smooth_corr = (float *) volk_malloc(sizeof(float)*nitems, volk_get_alignment());

      // Create a Filter. First normalize the taps, then reverse conjugate them.
      std::vector<gr_complex> pseq_filt(&d_frame->pseq_vec[0][0], &d_frame->pseq_vec[0][d_frame->len[0]]);
      utils::normalize(&pseq_filt[0], pseq_filt.size());
      utils::conj(&pseq_filt[0], pseq_filt.size());
      std::reverse(pseq_filt.begin(), pseq_filt.end());
      d_filter = new gr::filter::kernel::fft_filter_ccc(1, pseq_filt);

      // arrays needed to compute the normalization
      d_in_mag2 = (float*) volk_malloc(sizeof(float)*nitems, volk_get_alignment());
      d_mavg_mag2 = (float*) volk_malloc(sizeof(float)*(nitems+1024), volk_get_alignment());
      std::fill(&d_mavg_mag2[0], &d_mavg_mag2[d_frame->n_repeats[0]*d_frame->len[0]], 1); // fill the history with ones
      std::vector<float> ones_vec(d_frame->awgn_len,1);
      // d_filter2 = new gr::filter::kernel::fft_filter_fff(1, ones_vec);
      // d_filter2->set_taps(ones_vec);
      awgn_mavg = new volk_utils::moving_average<float>(d_frame->awgn_len);
      awgn_mavg->execute(&ones_vec[0],d_frame->awgn_len);
    }

    crosscorr_detector_cc::~crosscorr_detector_cc() {
      volk_free(d_corr);
      volk_free(d_corr_mag);
      volk_free(d_smooth_corr);
      volk_free(d_in_mag2);
      volk_free(d_mavg_mag2);
      delete d_filter;
      // delete d_filter2;
      delete awgn_mavg;
    }

    void crosscorr_detector_cc::work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn) {
      int len0 = d_frame->len[0];
      int n_repeats0 = d_frame->n_repeats[0];
      long d_corr_toffset = n_read + hist_len - len0 + 1;// points to absolute tstamp of beginning of filter

      // We first calculate the cross-correlation and mag2 it
      d_filter->filter(noutput_items, &in[hist_len], d_corr);
      volk_32fc_magnitude_squared_32f(&d_corr_mag[0], d_corr, noutput_items);

      // make an interleaved moving average as we know the peaks are at a similar distance
      d_interleaved_mavg.execute(&d_corr_mag[0], &d_smooth_corr[0], noutput_items);

      // Find the magnitude squared of the original signal and average it
      volk_32fc_magnitude_squared_32f(&d_in_mag2[0], &in[hist_len], noutput_items);
      // d_filter2->filter(noutput_items, &d_in_mag2[0], &d_mavg_mag2[n_repeats0*len0]);
      awgn_mavg->execute(&d_in_mag2[0], &d_mavg_mag2[n_repeats0*len0], noutput_items);
      // std::cout << "d_sum: " << awgn_mavg->mean() << std::endl;
      // NOTE: we divide by a delayed power of the signal. We expect that the samples before the preamble are
      // just noise/uncontaminated

      // If we find a peak in the smoothed crosscorr, we may have found the preamble
      // Analyze sections of length frame_period at a time.
      for(int section_idx = 0; section_idx < noutput_items; section_idx += d_frame->frame_period) {
        int max_n = std::min((long int)noutput_items-section_idx, d_frame->frame_period);
        unsigned short midx;
        volk_32f_index_max_16u(&midx, d_smooth_corr + section_idx, max_n);
        // TODO: Check if using a max actually provides acceptable results or i should find local max instead
        unsigned int max_i = section_idx + midx;
       
        float peak_corr = d_smooth_corr[max_i] / len0;  // This is the mean power of the corr smoothed across repeats
        float awgn_estim = d_mavg_mag2[max_i], peak_mag2 = d_mavg_mag2[max_i+n_repeats0*len0];// / d_frame->awgn_len;
        long peak_idx = d_corr_toffset + max_i;

        if(peak_corr > d_thres*awgn_estim && is_existing_peak(peak_idx)==false) { // d_thres*d_awgn
          std::cout << "STATUS: Peak detected: {" << peak_idx << "," << peak_corr << ","
                    << awgn_estim << "}" << std::endl;
          int p_;
          for(p_ = 0; p_ < peaks.size(); ++p_) {
            if(peaks[p_].idx + len0 == peak_idx) {
              // if there was an increase relatively to last peak
              if(peaks[p_].corr_val < d_smooth_corr[max_i]) {
                peaks[p_].idx = peak_idx;
                peaks[p_].corr_val = peak_corr;
                peaks[p_].peak_mag2 = peak_mag2;
                peaks[p_].awgn_estim = awgn_estim;
                std::cout << "DEBUG: Updating peak. New peak position: " << peak_idx << std::endl;
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
            detection_instance new_peak(d_frame->n_repeats[0]-1);
            // go back several positions to start computing the autocorrelation
            assert(hist_len+1-(n_repeats0*len0) >= 0);

            int past_idx = (int)hist_len+1 + (int)max_i - (int)(n_repeats0*len0);
            for(int k = 0; k < n_repeats0-1; ++k) {
              int idx = past_idx + k*len0, idx2 = idx + len0;
              gr_complex res;
              volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in[idx], &in[idx2], len0);
              res /= len0;
              new_peak.schmidl_vals.execute(res);
              // std::cout << "max_i:" << max_i << ",idx:" << idx << ",in[idx]:" << in[idx] << std::endl;
            }
            new_peak.idx = peak_idx;
            new_peak.corr_val = peak_corr;
            new_peak.peak_mag2 = peak_mag2;
            new_peak.awgn_estim = awgn_estim;
            peaks.push_back(new_peak);
            std::cout << "A peak candidate was found at " << new_peak.idx
                      << ": " << new_peak.corr_val << std::endl;
          }
          else if(peaks[p_].valid==false) {
            // the peak was updated. Update also its schmidl&cox phase
            int past_idx = std::max((int)hist_len+1+(int)max_i-(int)len0,0);
            gr_complex res;
            volk_32fc_x2_conjugate_dot_prod_32fc(&res,&in[past_idx],&in[(int)hist_len+(int)max_i], len0);
            res /= len0;
            peaks[p_].schmidl_vals.execute(res);
          }
        }

        // check for peaks to set them to true
        for(int p_ = 0; p_ < peaks.size(); ++p_)
          if(peaks[p_].valid==false && peaks[p_].idx + len0 <  d_corr_toffset + section_idx + d_frame->frame_period) {
            peaks[p_].valid = true;
            std::cout << "A peak solution was found at " << peaks[p_].idx
                      << ": " << peaks[p_].corr_val << std::endl;
          }

      }

      // move the unused values(due to the delay) to the start to be used as history in the next work() call
      std::copy(&d_mavg_mag2[noutput_items], &d_mavg_mag2[noutput_items+n_repeats0*len0], &d_mavg_mag2[0]);
    }

    bool crosscorr_detector_cc::is_existing_peak(long new_idx) {
      for(int p_ = 0; p_ < peaks.size(); ++p_) {
        long rots = round((new_idx - peaks[p_].idx)/(double)d_frame->frame_period)*d_frame->frame_period;
        int diff = abs(new_idx - (peaks[p_].idx + rots));
        if(diff < 5) {
          std::cout << "STATUS: Peak at " << new_idx << " is an already existing one. Going to ignore..." << std::endl;
          assert(peaks[p_].valid==true); // it should be already valid
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
      for(std::vector<detection_instance>::iterator it = peaks.begin(); it != peaks.end(); ++it) {
        w.StartObject();
        w.String("idx");
        w.Int(it->idx);
        w.String("corr_val");
        w.Double(it->corr_val);
        w.String("peak_mag2");
        w.Double(it->peak_mag2);
        w.String("schmidl_vals");
        w.StartArray();
        for(int i = 0; i < it->schmidl_vals.size(); ++i) {
          w.String(print_complex(it->schmidl_vals.d_vec[i]).c_str());
        }
        w.EndArray();
        w.String("schmidl_mean");
        w.String(print_complex(it->schmidl_vals.mean()).c_str());
        w.String("valid");
        w.Bool(it->valid);
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
