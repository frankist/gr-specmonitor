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

#include "tracked_peak.h"
#include <gnuradio/filter/fft_filter.h>
#include "utils/digital/moving_average.h"
#include <volk/volk.h>
#include "utils/math/operation.h"
#include "utils/math/transform.h"
#include <numeric>

#ifndef _CROSSCORR_TRACKER_CC_H_
#define _CROSSCORR_TRACKER_CC_H_

namespace gr {
  namespace specmonitor {
    /**
     * Find the crosscorr maximum in a window of size N
     */
    std::pair<int,float> find_crosspeak(const gr_complex* v, const gr_complex* pseq, int seq_len, int N) {
      int max_idx = -1;
      float max_val = -1;
      // std::cout << "crosscorr: [";
      for(int i = 0; i < N; ++i) {
        gr_complex res;
        volk_32fc_x2_conjugate_dot_prod_32fc(&res, &v[i], &pseq[0], seq_len);
        if(std::norm(res) > max_val) {
          max_val = std::norm(res);
          max_idx = i;
        }
        // std::cout << std::norm(res)/seq_len << ",";
      }
      // std::cout << "]" << std::endl;
      return std::make_pair(max_idx,max_val/seq_len);
    }

    class crosscorr_tracker {
    public:
      // arguments
      frame_params* d_frame_ptr;
      float d_thres;
      int d_corr_margin;

      // derived
      volk_utils::volk_array<gr_complex> d_preamble;
      int d_seq1_offset;

      // internal
      gr_complex* d_in_cfo;
      std::vector<tracked_peak> d_peaks;
      enum TrackState {AWGN, CFO, TOFFSET};
      TrackState d_state;

      crosscorr_tracker(frame_params* frame_ptr,
                        float thres);
      ~crosscorr_tracker();
      bool try_update_cfo(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int n_read);
      bool try_update_toffset(const utils::hist_array_view<const gr_complex>& in_h,
                              int noutput_items, int n_read);
      bool try_update_awgn(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int n_read);
      void try_erase_peaks();
      bool is_existing_peak(long new_idx);
      std::vector<tracked_peak>::iterator try_insert_peak(const preamble_peak& p);
      void work(const utils::hist_array_view<const gr_complex>& in_h, int noutput_items, int n_read);
      void to_json(rapidjson::PrettyWriter<rapidjson::StringBuffer> &w);
    };


    crosscorr_tracker::crosscorr_tracker(frame_params* frame_ptr,
                                         float thres) :
      d_frame_ptr(frame_ptr),
      d_thres(thres),
      d_corr_margin(2),
      d_state(crosscorr_tracker::TOFFSET) {
      assert(d_frame_ptr->len[1]>0);
      size_t cap = (size_t)ceil((d_frame_ptr->len[1]+2*d_corr_margin) / 1024.0f)*1024;
      d_in_cfo = (gr_complex *) volk_malloc(sizeof(gr_complex)*cap, volk_get_alignment());
      d_seq1_offset = d_frame_ptr->len[0] * d_frame_ptr->n_repeats[0];

      // create the total preamble
      compute_preamble(d_preamble, *d_frame_ptr);
      // std::cout << container::print(&d_preamble[0], &d_preamble[d_preamble.capacity()]) << std::endl;
    }

    crosscorr_tracker::~crosscorr_tracker() {
      volk_free(d_in_cfo);
    }

    std::vector<tracked_peak>::iterator crosscorr_tracker::try_insert_peak(const preamble_peak& p) {
      if(is_existing_peak(p.tidx))
        return d_peaks.end();
      tracked_peak c(p);
      d_peaks.push_back(c);
      return d_peaks.end()-1;
    }

    bool crosscorr_tracker::try_update_awgn(const utils::hist_array_view<const gr_complex>& in_h,
                                            int noutput_items, int n_read) {
      int len0 = d_frame_ptr->len[0];
      bool peak_updated = false;
      for(int i = 0; i < d_peaks.size(); ++i) {
        if(d_peaks[i].d_state != tracked_peak::AWGN)
          continue;
        int next_pseq0 = d_peaks[i].preamble_idx() - n_read;
        int next_awgn_win = next_pseq0 - d_frame_ptr->awgn_len;

        if(next_pseq0 >= 0 && next_pseq0 < noutput_items) {
          // computes the sum(abs()**2)
          gr_complex res;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in_h[next_awgn_win], &in_h[next_awgn_win], d_frame_ptr->awgn_len);
          float mean_pwr = std::abs(res)/d_frame_ptr->awgn_len;
          // std::cout << "DEBUG: Updating AWGN for preamble starting at " << next_pseq0 << " to " << mean_pwr << std::endl;
          d_peaks[i].update_awgn(mean_pwr);
          peak_updated = true;
        }
      }
    }

    bool crosscorr_tracker::try_update_cfo(const utils::hist_array_view<const gr_complex>& in_h,
                                           int noutput_items, int n_read) {
      int len0 = d_frame_ptr->len[0];
      bool peak_updated = false;
      for(int i = 0; i < d_peaks.size(); ++i) {
        if(d_peaks[i].d_state != tracked_peak::CFO)
          continue;
        int next_pseq0 = d_peaks[i].preamble_idx() - n_read;
        int next_end_pseq0 = next_pseq0 + 2*len0; // points at the end of two seq0

        if(next_end_pseq0 >= 0 && next_end_pseq0 < noutput_items) {
          gr_complex res;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in_h[next_pseq0],
                                               &in_h[next_pseq0+len0], len0);
          // std::cout << "DEBUG: Correcting CFO for preamble starting at " << next_pseq0 << ": " << std::arg(res)/(2*M_PI*len0) << std::endl;
          res = (std::abs(res)/len0)*std::exp(gr_complex(0,std::arg(res)/len0));
          d_peaks[i].update_cfo(res);
          peak_updated = true;
        }
      }
    }

    bool crosscorr_tracker::try_update_toffset(const utils::hist_array_view<const gr_complex>& in_h,
                                               int noutput_items, int n_read) {
      int len1 = d_frame_ptr->len[1];
      bool peak_updated = false;

      for(int i = 0; i < d_peaks.size(); ++i) {
        if(d_peaks[i].d_state != tracked_peak::TOFFSET)
          continue;

        int end_idx = d_peaks[i].preamble_idx() - n_read + d_preamble.capacity() + d_corr_margin; // points at the end of preamble + corr-margin
        int pseq1_idx = d_peaks[i].preamble_idx() - n_read + d_seq1_offset;
        // assert(end_idx==(pseq1_idx + len1 + d_corr_margin)); // points at the end of preamble + corr-margin

        if(end_idx >= 0 && end_idx < noutput_items) {
          // compute the time offset through auto-correlation and update
          int start_idx = pseq1_idx - d_corr_margin;

          // compensate the CFO in the original signal
          volk_utils::compensate_cfo(d_in_cfo, &in_h[start_idx], d_peaks[i].cfo(), len1+2*d_corr_margin);
          assert(start_idx+len1+2*d_corr_margin<=in_h.d_size);

          // find peak within the window [-d_corr_margin,d_corr_margin] in next_pseq1
          std::pair<int,float> peak_pair = find_crosspeak(d_in_cfo, &d_frame_ptr->pseq_vec[1][0],
                                                          len1, 2*d_corr_margin);
          long observed_peak = peak_pair.first + start_idx + n_read - d_seq1_offset;
          std::cout << "DEBUG: The preamble (through crosscorr peak1) was detected at "
                    << observed_peak << ", with amp: " << peak_pair.second << std::endl;
          
          // Compute the absolute mag2
          gr_complex res;
          int block_idx = peak_pair.first + start_idx;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in_h[block_idx], &in_h[block_idx], len1);
          float mean_mag2 = std::abs(res)/len1;

          d_peaks[i].update_toffset(observed_peak, peak_pair.second, mean_mag2, d_thres, d_frame_ptr->frame_period);
          std::cout << "peak updated: " << println(d_peaks[i]) << std::endl;
          // update the peak for next frame
          d_peaks[i].increment_preamble_idx(d_frame_ptr->frame_period);
          peak_updated = true;
        }
      }
      // erase right away peaks that are not of good quality
      if(peak_updated)
        try_erase_peaks();
      return peak_updated;
    }

    void crosscorr_tracker::work(const utils::hist_array_view<const gr_complex>& in_h,
                                 int noutput_items, int n_read) {
      bool peaks_updated = true;
      // std::cout << "DEBUG: noutput_items=" << noutput_items << std::endl;

      while(peaks_updated==true) {
        peaks_updated = false;
        peaks_updated |= try_update_awgn(in_h, noutput_items, n_read);
        peaks_updated |= try_update_cfo(in_h, noutput_items, n_read);
        peaks_updated |= try_update_toffset(in_h, noutput_items, n_read);
      }

      std::cout << "YOLOLO " << d_peaks.size() << std::endl;
    }

    bool test_peak_remove(const tracked_peak& p) {
      bool ret = p.n_frames_elapsed>=1 && p.n_frames_detected==0; // the first peak was missed
      ret = ret || p.n_missed_frames_contiguous>4; // there are two many frames being missed
      // ret = ret || p.crosscorr_mag()/p.awgn_power() < 1.0;
      if(ret)
        std::cout << "Going to remove peak:" << p.n_frames_detected
                << "," << p.n_frames_elapsed << "," << println(p) << std::endl;
      return ret;
    }

    void crosscorr_tracker::try_erase_peaks() {
      d_peaks.erase(std::remove_if(d_peaks.begin(), d_peaks.end(), test_peak_remove), d_peaks.end());
    }


    bool crosscorr_tracker::is_existing_peak(long new_idx) {
      for(int p_ = 0; p_ < d_peaks.size(); ++p_) {
        long rots = round((new_idx - d_peaks[p_].preamble_idx())/(double)d_frame_ptr->frame_period)*d_frame_ptr->frame_period;
        int diff = abs(new_idx - (d_peaks[p_].preamble_idx() + rots));
        if(diff < 5) {
          std::cout << "DEBUG: Peak at " << new_idx
                    << " is an already existing one. Going to ignore..." << std::endl;
          return true;
        }
      }
      return false;
    }

    void crosscorr_tracker::to_json(rapidjson::PrettyWriter<rapidjson::StringBuffer> &w) {
      std::cout << "WOLOLOLOLOLOLOLOLO " << d_peaks.size() << std::endl;
      w.StartArray();
      for(int i = 0; i < d_peaks.size(); ++i) {
        w.StartObject();
        w.String("peak_idx");
        w.Int(d_peaks[i].preamble_idx());
        w.String("peak_corr");
        w.Double(d_peaks[i].crosscorr_mag());
        w.String("peak_mag2");
        w.Double(d_peaks[i].preamble_power());
        w.String("cfo");
        w.Double(d_peaks[i].cfo());
        w.String("awgn_estim");
        w.Double(d_peaks[i].awgn_power());
        w.String("n_frames_elapsed");
        w.Int(d_peaks[i].n_frames_elapsed);
        w.String("n_frames_detected");
        w.Int(d_peaks[i].n_frames_detected);
        w.EndObject();
      }
      w.EndArray();
    }
  }
}

#endif
