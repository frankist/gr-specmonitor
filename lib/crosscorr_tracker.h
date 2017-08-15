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

    class tracked_peak {
    public:
      double peak_idx;
      float peak_amp;
      float cfo;
      float awgn_estim;
      int n_frames_elapsed;
      int n_frames_detected;
      bool first_flag;

      tracked_peak() : n_frames_elapsed(0), n_frames_detected(0), first_flag(true) {}
      void update_toffset(long new_peak, float corramp, float thres, long frame_period);
      void update_cfo(gr_complex res, int len0);
      void update_awgn(float new_awgn);
    };

    class crosscorr_tracker {
    public:
      // arguments
      frame_params* d_frame_ptr;
      float d_thres;
      int d_corr_margin;

      // derived
      int d_seq1_offset;

      // internal
      gr_complex* d_in_cfo;
      std::vector<tracked_peak> d_peaks;
      enum TrackState {AWGN, CFO, TOFFSET};
      TrackState d_state;

      crosscorr_tracker(frame_params* frame_ptr,
                        float thres);
      ~crosscorr_tracker();
      bool try_update_cfo(const gr_complex* in, int noutput_items, int n_read);
      bool try_update_toffset(const gr_complex *in, int noutput_items, int n_read, float awgn);
      bool try_update_awgn(const gr_complex* in, int noutput_items, int n_read);
      void insert_peak(const detection_instance& p);
      void work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn);
      void to_json(rapidjson::PrettyWriter<rapidjson::StringBuffer> &w);
    };

    void tracked_peak::update_toffset(long new_peak, float corramp, float thres, long frame_period) {
      if(corramp > thres) {
        if(first_flag==true) {
          peak_amp = corramp;
          peak_idx = new_peak;
          first_flag = false;
        }
        else {
          peak_idx = 0.95*peak_idx + 0.05*new_peak;
          peak_amp = 0.95*peak_amp + 0.05*corramp;
        }
        n_frames_detected++;
      }
      else {
        std::cout << "WARNING: The peak was missed. The crosscorr params were: {"
                  << new_peak << "," << corramp << "}"  << std::endl;
      }
    }

    void tracked_peak::update_cfo(gr_complex res, int len0) {
      float cfo_new = std::arg(res)/(2*M_PI*len0);
      cfo = 0.95*cfo + 0.05*cfo_new;
    }

    void tracked_peak::update_awgn(float new_awgn) {
      awgn_estim = 0.95*awgn_estim + 0.05*new_awgn;
    }

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
    }

    crosscorr_tracker::~crosscorr_tracker() {
      volk_free(d_in_cfo);
    }

    void crosscorr_tracker::insert_peak(const detection_instance& p) {
      tracked_peak c;
      c.peak_idx = p.idx - (d_frame_ptr->n_repeats[0]-1)*d_frame_ptr->len[0]; // points to beginning of preamble
      c.peak_amp = p.corr_val;
      c.cfo = -std::arg(p.schmidl_vals.mean())/(2*M_PI*d_frame_ptr->len[0]);
      c.awgn_estim = p.awgn_estim;
      std::cout << "DEBUG: Gonna create tracked peak {" << c.peak_idx << ","
                << c.peak_amp << "," << c.cfo << "}" << std::endl;
      d_peaks.push_back(c);
    }

    bool crosscorr_tracker::try_update_awgn(const gr_complex* in, int noutput_items, int n_read) {
      int len0 = d_frame_ptr->len[0];
      bool peak_updated = false;
      for(int i = 0; i < d_peaks.size(); ++i) {
        int next_pseq0 = d_peaks[i].peak_idx - n_read;
        int next_awgn_win = next_pseq0 - d_frame_ptr->awgn_len;

        if(next_pseq0 >= 0 && next_pseq0 < noutput_items) {
          std::cout << "DEBUG: Updating Amp for preamble starting at " << next_pseq0 << std::endl;
          // computes the sum(abs()**2)
          gr_complex res;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in[next_awgn_win], &in[next_awgn_win], d_frame_ptr->awgn_len);
          float mean_pwr = std::norm(res)/d_frame_ptr->awgn_len;
          d_peaks[i].update_awgn(mean_pwr);
          d_state = crosscorr_tracker::CFO;
          peak_updated = true;
        }
      }
    }

    bool crosscorr_tracker::try_update_cfo(const gr_complex* in, int noutput_items, int n_read) {
      int len0 = d_frame_ptr->len[0];
      bool peak_updated = false;
      for(int i = 0; i < d_peaks.size(); ++i) {
        int next_pseq0 = d_peaks[i].peak_idx - n_read;
        int next_end_pseq0 = next_pseq0 + 2*len0; // points at the end of two seq0

        if(next_end_pseq0 >= 0 && next_end_pseq0 < noutput_items) {
          std::cout << "DEBUG: Correcting CFO for preamble starting at " << next_pseq0 << std::endl;
          gr_complex res;
          volk_32fc_x2_conjugate_dot_prod_32fc(&res, &in[next_pseq0],
                                               &in[next_pseq0+len0], len0);
          d_peaks[i].update_cfo(res, len0);
          d_state = crosscorr_tracker::TOFFSET;
          peak_updated = true;
        }
      }
    }

    bool crosscorr_tracker::try_update_toffset(const gr_complex *in, int noutput_items, int n_read, float awgn) {
      int len1 = d_frame_ptr->len[1];
      bool peak_updated = false;

      for(int i = 0; i < d_peaks.size(); ++i) {
        int pseq1_idx = d_peaks[i].peak_idx - n_read + d_seq1_offset;
        int end_idx = pseq1_idx + len1 + d_corr_margin; // points at the end of preamble + corr-margin

        if(end_idx >= 0 && end_idx < noutput_items) {
          // compute the time offset through auto-correlation and update
          int start_idx = pseq1_idx - d_corr_margin;

          // compensate the CFO in the original signal
          lv_32fc_t phase_increment = lv_cmake(std::cos(d_peaks[i].cfo),std::sin(d_peaks[i].cfo));
          lv_32fc_t phase_init = lv_cmake(1.0f,0.0f);
          volk_32fc_s32fc_x2_rotator_32fc(d_in_cfo, &in[start_idx], phase_increment, &phase_init,
                                          len1 + 2*d_corr_margin);

          // find peak within the window [-d_corr_margin,d_corr_margin] in next_pseq1
          std::pair<int,float> peak_pair = find_crosspeak(d_in_cfo, d_frame_ptr->pseq_vec[1],
                                                          len1, 2*d_corr_margin);
          long observed_peak = peak_pair.first + start_idx + n_read - d_seq1_offset;
          std::cout << "DEBUG: The preamble (through crosscorr peak1) was detected at "
                    << observed_peak << ", with amp: " << peak_pair.second << std::endl;

          d_peaks[i].update_toffset(observed_peak, peak_pair.second, awgn, d_frame_ptr->frame_period);

          // update the peak for next frame
          d_peaks[i].peak_idx += d_frame_ptr->frame_period;
          d_peaks[i].n_frames_elapsed++;
          d_state = crosscorr_tracker::AWGN;
          peak_updated = true;
        }
      }
      return peak_updated;
    }

    void crosscorr_tracker::work(const gr_complex* in, int noutput_items, int hist_len, int n_read, float awgn) {
      bool peaks_updated = true;
      std::cout << "DEBUG: noutput_items=" << noutput_items << std::endl;

      while(peaks_updated==true) {
        switch(d_state) {
        case crosscorr_tracker::AWGN: // update the AWGN estimate with noise samples before preamble
          peaks_updated = try_update_awgn(in, noutput_items, n_read);
        case crosscorr_tracker::CFO: // compute Schmidl&Cox and update cfo
          peaks_updated = try_update_cfo(in, noutput_items, n_read);
        case crosscorr_tracker::TOFFSET: // compute the time offset through cross-correlation and update
          peaks_updated = try_update_toffset(in, noutput_items, n_read, awgn);
        }
      }
    }

    void crosscorr_tracker::to_json(rapidjson::PrettyWriter<rapidjson::StringBuffer> &w) {
      w.StartArray();
      for(int i = 0; i < d_peaks.size(); ++i) {
        w.StartObject();
        w.String("peak_idx");
        w.Int((long)d_peaks[i].peak_idx);
        w.String("peak_amp");
        w.Double(d_peaks[i].peak_amp);
        w.String("cfo");
        w.Double(d_peaks[i].cfo);
        w.String("awgn_estim");
        w.Double(d_peaks[i].awgn_estim);
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
