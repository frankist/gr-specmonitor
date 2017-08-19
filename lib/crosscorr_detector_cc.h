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
#include "utils/digital/range_utils.h"

#ifndef _CROSSCORR_DETECTOR_CC_H_
#define _CROSSCORR_DETECTOR_CC_H_

namespace gr {
  namespace specmonitor {
    class frame_params {
    public:
      // std::vector<gr_complex*> pseq_vec;
      std::vector<volk_utils::volk_array<gr_complex> > pseq_vec;
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
          // pseq_vec[i] = (gr_complex*) volk_malloc(sizeof(gr_complex)*len[i], volk_get_alignment());
          pseq_vec[i].resize(len[i]);
          std::copy(&p_vec[i][0], &p_vec[i][len[i]], &pseq_vec[i][0]);
          utils::normalize(&pseq_vec[i][0], len[i]);
        }
        n_repeats = n_r;
      }
      // ~frame_params() {
      //   for(int i = 0; i < pseq_vec.size(); ++i) {
      //     volk_free(pseq_vec[i]);
      //   }
      // }
      int preamble_duration() const {
        int sum = 0;
        for(int i = 0; i < len.size(); ++i)
          sum += len[i]*n_repeats[i];
        return sum;
      }
    private:
      frame_params(const frame_params& f) {} // deleted
      frame_params& operator=(const frame_params& f) {} // deleted
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
      detection_instance(long idx_x, float corr, float mag2, float awgn, int siz) :
        idx(idx_x), corr_val(corr), peak_mag2(mag2), awgn_estim(awgn),
        schmidl_vals(siz), valid(false), tracked(false) {}
      static bool idx_compare(const detection_instance& a, const detection_instance& b) {return a.idx < b.idx;}
      static bool is_valid(const detection_instance& a) {return a.valid;}
    };

    class crosscorr_detector_cc {
    public:
      const frame_params* d_frame;
      float d_thres;

      // derived
      int d_len0;
      int d_len0_tot;

      volk_utils::volk_array<gr_complex> d_corr;
      volk_utils::volk_array<float> d_corr_mag;
      volk_utils::volk_array<float> d_smooth_corr;
      // volk_utils::volk_array<float> d_in_mag2;
      // volk_utils::volk_array<float> d_mavg_mag2;
      // volk_utils::volk_array<float> d_preamble_mag2;
      interleaved_moving_average d_interleaved_mavg;
      gr::filter::kernel::fft_filter_ccc* d_filter;
      // volk_utils::moving_average<float> *awgn_mavg;
      // volk_utils::moving_average<float> *d_preamble_mag2_mavg;
      int d_smooth_corr_h_len;
      int d_mavg_mag2_hist_len;
      std::vector<detection_instance> peaks;
      std::vector<detection_instance> peaks_in_buffer;

      // utils::hist_array_view<float> d_awgn_mag2_hist;
      utils::hist_array_view<float> d_smooth_corr_h;
      // utils::hist_array_view<float> d_preamble_mag2_hist;

      volk_utils::volk_array<float> d_xmag2;
      utils::hist_array_view<float> d_xmag2_h;
      // internal state
      int d_kk_start;

      crosscorr_detector_cc(const frame_params* f_params, int nitems, float thres, float awgn_guess = 1);

      ~crosscorr_detector_cc();

      void compute_autocorr(detection_instance& new_peak, const gr_complex* in, int hist_len, int max_i);
      void work(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int hist_len, int n_read, float awgn);
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
                                                 int nitems, float thres, float awgn_guess) :
      d_frame(f_params), d_thres(thres), 
      d_len0(f_params->len[0]),
      d_len0_tot(f_params->len[0]*f_params->n_repeats[0]),
      d_interleaved_mavg(f_params->len[0],f_params->n_repeats[0]),
      d_kk_start(0) {
      d_smooth_corr_h_len = d_len0_tot - d_len0 + 1;
      d_mavg_mag2_hist_len = d_smooth_corr_h_len + d_frame->len[0]*d_frame->n_repeats[0];

      // this will compute the crosscorr with peak0
      d_corr.resize(nitems);
      d_corr_mag.resize(nitems);
      d_smooth_corr.resize(nitems + d_smooth_corr_h_len);
      std::fill(&d_smooth_corr[0],&d_smooth_corr[d_smooth_corr_h_len], 0);
      d_smooth_corr_h.set(&d_smooth_corr[0], d_smooth_corr_h_len);

      // Create a Filter. First normalize the taps, then reverse conjugate them.
      std::vector<gr_complex> pseq_filt(&d_frame->pseq_vec[0][0], &d_frame->pseq_vec[0][d_frame->len[0]]);
      utils::normalize(&pseq_filt[0], pseq_filt.size());
      utils::conj(&pseq_filt[0], pseq_filt.size());
      std::reverse(pseq_filt.begin(), pseq_filt.end());
      d_filter = new gr::filter::kernel::fft_filter_ccc(1, pseq_filt);

      // We keep the mag2 of the received signal to compute the energy and AWGN
      d_xmag2.resize(nitems+1024*2);
      d_xmag2_h.set(&d_xmag2[0], d_smooth_corr_h_len + d_len0_tot + d_frame->awgn_len);
      std::fill(&d_xmag2[0],&d_xmag2[d_xmag2_h.hist_len], awgn_guess);
    }

    crosscorr_detector_cc::~crosscorr_detector_cc() {
      delete d_filter;
    }

    void crosscorr_detector_cc::compute_autocorr(detection_instance& new_peak, const gr_complex* in, int hist_len,
                                                 int max_i) {
      assert(hist_len+1-d_len0_tot >= 0);
      int past_idx = hist_len + 1 + max_i - d_len0_tot; // look back to the beginning of the preamble
      for(int k = 0; k < d_frame->n_repeats[0]-1; ++k) {
        int idx = past_idx + k*d_len0, idx2 = idx + d_len0;
        gr_complex res;
        volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in[idx], &in[idx2], d_len0);
        res /= d_len0;
        new_peak.schmidl_vals.execute(res);
        // std::cout << "max_i:" << max_i << ",idx:" << idx << ",in[idx]:" << in[idx] << std::endl;
      }
    }

    class remove_idx_cmp {
    public:
      long idx;
      remove_idx_cmp(long idx_x) : idx(idx_x) {}
      bool operator()(const detection_instance& d) const {return d.idx < idx; }
    };

    void crosscorr_detector_cc::work(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int hist_len, int n_read, float awgn) {
      int n_repeats0 = d_frame->n_repeats[0];
      long d_corr_toffset = n_read + hist_len - d_len0 + 1 - d_smooth_corr_h_len;// points to absolute tstamp of beginning of filter

      // We first calculate the cross-correlation and mag2 it
      d_filter->filter(noutput_items, &in_h[0], &d_corr[0]);
      volk_32fc_magnitude_squared_32f(&d_corr_mag[0], &d_corr[0], noutput_items);

      // make an interleaved moving average as we know the peaks are at a similar distance
      d_interleaved_mavg.execute(&d_corr_mag[0], &d_smooth_corr_h[0], noutput_items);

      // Find the magnitude squared of the original signal and average it
      volk_32fc_magnitude_squared_32f(&d_xmag2_h[0], &in_h[0], noutput_items);
      // NOTE: we divide by a delayed power of the signal. We expect that the samples before the preamble are
      // just noise/uncontaminated
      std::cout << "DEBUG: window: [" << d_corr_toffset << "," << d_corr_toffset+noutput_items << "], noutput_items: " << noutput_items << std::endl;

      int kk;
      for(kk = d_kk_start; kk < noutput_items; ++kk) {
        float *xcorr_ptr = &d_smooth_corr_h[kk-d_smooth_corr_h.hist_len]; // this points to the d_smooth_corr point under analysis. (It can be in history)
        float *xmag2_ptr = &d_xmag2_h[kk-d_smooth_corr_h.hist_len-d_len0_tot+1];
        float *awgn_ptr = &d_xmag2_h[kk-d_smooth_corr_h.hist_len-d_len0_tot-d_frame->awgn_len+1];

        float peak_corr = xcorr_ptr[0] / d_len0;  // This is the mean power of the corr smoothed across repeats.
        long peak_idx = d_corr_toffset + kk;
        float peak_mag2 = std::accumulate(xmag2_ptr,xmag2_ptr + d_len0_tot,0.0)/d_len0_tot;
        float awgn_estim = std::accumulate(awgn_ptr,awgn_ptr + d_frame->awgn_len,0.0)/d_frame->awgn_len;
        gr_complex res;
        // const gr_complex *pin = &in_h[kk-d_smooth_corr_h.hist_len+1-d_len0_tot];
        // volk_32fc_x2_conjugate_dot_prod_32fc(&res, pin, pin, d_len0_tot);
        // float peak_mag2_3 = std::abs(res)/d_len0_tot;

        // if(peak_mag2_2>1.01e-6)
        //   std::cout << peak_mag2_2 << "," << peak_mag2 << "," << peak_corr << std::endl;
        // assert(abs(peak_mag2_2/peak_mag2-1)<0.0000001);// && 0);
        // assert(abs(awgn_mag2_2/awgn_estim-1)<0.0000001);
        // assert(abs(peak_mag2_2-peak_mag2_3)<0.00001);// && 0);

        if(peak_corr > d_thres*awgn_estim) {//peak_mag2 && peak_mag2 > d_thres2*awgn_estim) {
          // FIXME: change to peak_mag2. Current peak_mag2 is the average over awgn_len and not the preamble size
          // NOTE: i don't use AWGN for normalization, as it would make my detector sensitive to the energy of the sent signal
          unsigned short midx;
          volk_32f_index_max_16u(&midx, xcorr_ptr + 1, d_smooth_corr_h.hist_len-1);
          int max_i = kk + 1 + midx;
          if(xcorr_ptr[0] < xcorr_ptr[(int)midx+1]) { // it is just a local optimum
            kk = max_i - 1; // kk is going to be incremented
            continue;
          }

          if(is_existing_peak(peak_idx) == false) {
            detection_instance peak_inst(peak_idx, peak_corr, peak_mag2, awgn_estim, d_frame->n_repeats[0]-1);
            compute_autocorr(peak_inst, in_h.vec, hist_len, kk-d_smooth_corr_h_len);

            peak_inst.valid = true; // TODO: Remove this parameter
            peaks.push_back(peak_inst);
            std::cout << "STATUS: Crosscorr Peak0 detected: {" << peak_idx << "," << peak_corr << ","
                      << awgn_estim << "," << peak_mag2 << "," << peak_inst.schmidl_vals.mean() << "}" << std::endl;
          }
          kk += d_smooth_corr_h.hist_len + d_len0 + d_frame->len[1];  // skip the margin examined, plus the pseq1, as the crosscorr(pseq0,pseq1) may not be zero, and the detector may get a false positive
        }
      }

      // NOTE: if there was a hop bigger than the block, we do not continue from position kk=0 in the next call
      d_kk_start = kk-noutput_items;

      // // If we find a peak in the smoothed crosscorr, we may have found the preamble
      // // Analyze sections of length frame_period at a time.
      // for(int section_idx = 0; section_idx < noutput_items; section_idx += d_frame->frame_period) {
      //   int max_n = std::min((long int)noutput_items-section_idx, d_frame->frame_period);
      //   std::cout << "Find max in window: [" << section_idx+d_corr_toffset << "," << section_idx+d_corr_toffset+max_n << "]" << std::endl;
      //   unsigned short midx;
      //   volk_32f_index_max_16u(&midx, d_smooth_corr + section_idx, max_n);
      //   // TODO: Check if using a max actually provides acceptable results or i should find local max instead
      //   unsigned int max_i = section_idx + midx;
       
      //   float peak_corr = d_smooth_corr[max_i] / len0;  // This is the mean power of the corr smoothed across repeats
      //   float awgn_estim = d_mavg_mag2[max_i], peak_mag2 = d_mavg_mag2[max_i+n_repeats0*len0];// / d_frame->awgn_len;
      //   long peak_idx = d_corr_toffset + max_i;
      //   bool thres_passed = peak_corr > d_thres*awgn_estim;
      //   bool local_maximum = max_i + len0 >= section_idx + max_n;

      //   if(thres_passed && is_existing_peak(peak_idx)==false) { // d_thres*d_awgn
      //     detection_instance peak_inst(peak_idx, peak_corr, peak_mag2, awgn_estim, d_frame->n_repeats[0]-1);
      //     compute_autocorr(peak_inst, in, hist_len, (int)max_i, n_repeats0, len0);

      //     // check if we are not at the end of the section. If so, leave the peak in a buffer
      //     if(local_maximum) {
      //       peaks_in_buffer.push_back(peak_inst);
      //       std::cout << "DEBUG: Found a peak at " << peak_idx
      //                 << ", however it is at the end of the section window" << std::endl;
      //       continue;
      //     }

      //     // check for peaks in the buffer to see if they are not just a local maxima
      //     for(int pp = 0; pp < peaks_in_buffer.size(); ++pp) {
      //       if(peaks_in_buffer[pp].idx+len0 == peak_idx) { // TODO: Check if I should not add a margin to this comparison
      //         if(peaks_in_buffer[pp].corr_val < peak_inst.corr_val) { // there was not an increase
      //           std::cout << "DEBUG: Updating peak. New peak position: " << peak_idx << std::endl;
      //         }
      //         else {
      //           peak_inst = peaks_in_buffer[pp];
      //         }
      //         peaks_in_buffer.erase(peaks_in_buffer.begin()+pp);
      //         break;
      //       }
      //     }

      //     peak_inst.valid = true; // TODO: Remove this parameter
      //     peaks.push_back(peak_inst);
      //     std::cout << "STATUS: Peak detected: {" << peak_idx << "," << peak_corr << ","
      //               << awgn_estim << "}" << std::endl;
      //   }

      //   while(peaks_in_buffer.size()>0) {
      //     // if it is at the end of the section
      //     int block_idx_next = peaks_in_buffer.front().idx + len0 - d_corr_toffset;
      //     if(block_idx_next >= section_idx + max_n) // it is still cut
      //       break;
      //     float peak_corr_next = d_smooth_corr[block_idx_next] / len0;

      //     if(peak_corr_next >= peaks_in_buffer.front().corr_val) {
      //       std::cout << "DEBUG: The peak in the buffer was erased" << std::endl;
      //       // i am not gonna add the new one, as that should have been dealt with before
      //     }
      //     else {
      //       peaks.push_back(peaks_in_buffer.front());
      //       std::cout << "DEBUG: The peak in the buffer was actually a valid one" << std::endl;
      //     }
      //     peaks_in_buffer.erase(peaks_in_buffer.begin());
      //   }
      // }

          // int p_;
          // for(p_ = 0; p_ < peaks.size(); ++p_) {
          //   if(peaks[p_].idx + len0 == peak_idx) {
          //     // if there was an increase relatively to last peak
          //     if(peaks[p_].corr_val < d_smooth_corr[max_i]) {
          //       peaks[p_].idx = peak_idx;
          //       peaks[p_].corr_val = peak_corr;
          //       peaks[p_].peak_mag2 = peak_mag2;
          //       peaks[p_].awgn_estim = awgn_estim;
          //       std::cout << "DEBUG: Updating peak. New peak position: " << peak_idx << std::endl;
          //       std::sort(peaks.begin(),peaks.end(),detection_instance::idx_compare);
          //     }
          //     else {
          //       peaks[p_].valid = true;
          //       std::cout << "A peak solution was found at " << peaks[p_].idx
          //                 << ": " << peaks[p_].corr_val << std::endl;
          //     }
          //     break;
          //   }
          // }
        //   if(p_ == peaks.size()) { // this is a new peak hypothesis
        //     detection_instance new_peak(d_frame->n_repeats[0]-1);
        //     compute_autocorr(new_peak, in, hist_len, (int)max_i, n_repeats0, len0);
        //     peaks.push_back(new_peak);
        //     // std::cout << "A peak candidate was found at " << new_peak.idx
        //     //           << ": " << new_peak.corr_val << std::endl;
        //   }
        //   else if(peaks[p_].valid==false) {
        //     // the peak was updated. Update also its schmidl&cox phase
        //     int past_idx = std::max((int)hist_len+1+(int)max_i-(int)len0,0);
        //     gr_complex res;
        //     volk_32fc_x2_conjugate_dot_prod_32fc(&res,&in[past_idx],&in[(int)hist_len+(int)max_i], len0);
        //     res /= len0;
        //     peaks[p_].schmidl_vals.execute(res);
        //   }
        // }

        // check for peaks to set them to true
        // for(int p_ = 0; p_ < peaks.size(); ++p_)
        //   if(peaks[p_].valid==false && peaks[p_].idx + len0 <  d_corr_toffset + noutput_items) {
        //     peaks[p_].valid = true;
        //     std::cout << "A peak solution was found at " << peaks[p_].idx
        //               << ": " << peaks[p_].corr_val << std::endl;
        //     std::cout << peaks[p_].idx + len0 << "," << d_corr_toffset + noutput_items << std::endl;
        //   }

      // move the unused values(due to the delay) to the start to be used as history in the next work() call
      // std::copy(&d_mavg_mag2[noutput_items], &d_mavg_mag2[noutput_items+d_mavg_mag2_hist_len], &d_mavg_mag2[0]);
      // d_awgn_mag2_hist.advance(noutput_items);
      d_smooth_corr_h.advance(noutput_items);
      // d_preamble_mag2_hist.advance(noutput_items);//d_preamble_mag2_hist.hist_len);
      d_xmag2_h.advance(noutput_items);
      // std::copy(&d_smooth_corr[noutput_items], &d_smooth_corr[noutput_items+d_smooth_corr_h_len], &d_smooth_corr[0]);
      // std::copy(&d_preamble_mag2[noutput_items], &d_preamble_mag2[noutput_items+d_smooth_corr_h_len], &d_preamble_mag2[0]);
    }

    bool crosscorr_detector_cc::is_existing_peak(long new_idx) {
      for(int p_ = 0; p_ < peaks.size(); ++p_) {
        long rots = round((new_idx - peaks[p_].idx)/(double)d_frame->frame_period)*d_frame->frame_period;
        int diff = abs(new_idx - (peaks[p_].idx + rots));
        if(diff < 5) {
          std::cout << "DEBUG: Peak at " << new_idx
                    << " is an already existing one. Going to ignore..." << std::endl;
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
