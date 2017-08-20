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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "frame_sync_cc_impl.h"
#include <volk/volk.h>
#include "utils/serialization/rapidjson/stringbuffer.h"
#include "utils/serialization/rapidjson/prettywriter.h"
#include "utils/serialization/rapidjson/document.h"
#include "utils/prints/print_ranges.h"


namespace gr {
  namespace specmonitor {

    frame_sync_cc::sptr
    frame_sync_cc::make(const std::vector<std::vector<gr_complex> >& preamble_seq,
                        const std::vector<int>& n_repeats, float thres, long frame_period, int awgn_len, float awgn_guess)
    {
      return gnuradio::get_initial_sptr
        (new frame_sync_cc_impl(preamble_seq, n_repeats, thres, frame_period, awgn_len, awgn_guess));
    }

    /*
     * The private constructor
     */
    frame_sync_cc_impl::frame_sync_cc_impl(const std::vector<std::vector<gr_complex> >& preamble_seq,
                                           const std::vector<int>& n_repeats, float thres, long frame_period, int awgn_len, float awgn_guess)
      : gr::sync_block("frame_sync_cc",
                       gr::io_signature::make(1, 1, sizeof(gr_complex)),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
        d_frame(preamble_seq, n_repeats, frame_period, awgn_len),
        d_thres(thres),
        d_state(0)
    {
      // In order to easily support the optional second output,
      // don't deal with an unbounded max number of output items.
      // For the common case of not using the optional second output,
      // this ensures we optimally call the volk routines.
      const size_t nitems = 24*1024;
      set_max_noutput_items(nitems);

      d_crosscorr0 = new crosscorr_detector_cc(&d_frame, nitems, d_thres, awgn_guess);
      d_tracker = new crosscorr_tracker(&d_frame, d_thres);
      
      int hist_len = 2*d_frame.preamble_duration()+d_frame.awgn_len;//std::max(d_frame.n_repeats[0]*d_frame.len[0], d_frame.len[1]+2*5);
      //hist_len = std::max(hist_len,(int)d_frame.awgn_len);
      set_history(hist_len + 1);
    }

    bool test_peak_remove(const tracked_peak& p) {
      bool ret = p.n_frames_detected==1 && p.n_frames_detected==0; // the first peak was missed
      ret = ret || p.n_missed_frames_contiguous>4; // there are two many frames being missed
      ret = ret || p.peak_corr/p.awgn_estim < 1.0;
      return ret;
    }

    bool test_peak_accept(const tracked_peak& p) {
      return p.n_frames_detected>4 && p.n_frames_detected/p.n_frames_elapsed > 0.7 && p.snr()>1;
    }

    /*
     * Our virtual destructor.
     */
    frame_sync_cc_impl::~frame_sync_cc_impl()
    {
      delete d_crosscorr0;
      delete d_tracker;
      // std::cout << "DESTRUCTORRRRRRR MAIIIIIIN" << std::endl;
    }

    int
    frame_sync_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      // Our correlation filter length
      unsigned int hist_len = history()-1;
      const utils::hist_array_view<const gr_complex> in_h(in, hist_len, noutput_items);

      if(d_state==0)
        d_crosscorr0->work(in_h, noutput_items, hist_len, nitems_read(0), 1);

      std::vector<detection_instance> &v = d_crosscorr0->peaks;
      for(int i = 0; i < v.size(); ++i) {
        if(v[i].valid==true && v[i].tracked==false) {
          std::vector<tracked_peak>::iterator it = d_tracker->insert_peak(v[i]);
          dout << "STATUS: Found a new peak at " << it->peak_idx << ". Going to track it" << std::endl;
          v[i].tracked = true;
        }
      }

      // track the already detected peaks
      d_tracker->work(in, noutput_items, hist_len, nitems_read(0), 1);

      // erase peaks that are not of good quality
      std::vector<tracked_peak>& pvec = d_tracker->d_peaks;
      pvec.erase(std::remove_if(pvec.begin(), pvec.end(), test_peak_remove), pvec.end());

      if(d_state == 0) {
        for(int pp = 0; pp < d_tracker->d_peaks.size(); ++pp) {
          if(test_peak_accept(d_tracker->d_peaks[pp])) {
            dout << "STATUS: Found a good frame candidate: "
                 << println(d_tracker->d_peaks[pp]) << ". I will stop the crosscorr_detector" << std::endl;
            d_state = 1;
          }
        }
      }
      else if(d_state==1 && d_tracker->d_peaks.size()==0) {
        dout << "STATUS: Lost synchronization with frame candidates. Going to look for a new one" << std::endl;
      }

      //   std::vector<sync_hypothesis> &v = &hypothesis_vec[0];
      //   for(int i = 0; i < v.size(); ++i) {
      //     pseq2_start = v[i].idx + d_preamble_seq[0].size()*d_n_repeats[0];
      //     if(pseq2_start >= nitems_read(0) && pseq2_start < nitems_read(0) + noutput_items[0]) {
            
      //     }
      //   }
      // }

      // if(d_state==1) {
      //   d_filter0->filter(noutput_items, &in[hist_len], d_corr0);
      //   volk_32fc_magnitude_squared_32f(&d_corr0_mag[0], d_corr0, noutput_items);

      //   // computes the interleaved moving average to sum cross-corr peaks
      //   int interv_i = d_corr0_mavg_idx;
      //   for(int i = 0; i < noutput_items; ++i) {
      //     interv_i = (d_corr0_mavg_idx+i)%d_corr0_mavg_interleaved.size();
      //     d_corr0_mavg[i] = d_corr0_mavg_interleaved[interv_i].execute(d_corr0_mag[i]);
      //   }
      //   d_corr0_mavg_idx = interv_i;

      //   unsigned short max_i;
      //   volk_32f_index_max_16u(&max_i, d_corr0_mavg, noutput_items);
      //   if(d_corr0_mavg[max_i]>d_thres*d_awgn) {
      //     int autocorr_i = std::max((int)max_i - (int)(d_n_repeats[0]*d_seq0_len),0);
      //     for(int k = 0; k < d_seq0_len; ++k) {
      //       //FIXME: Check that it does not go over.
      //       //mult(&in[autocorr_i+k*d_seq0_len], np.conj(&in[autocorr_i + k*d_seq0_len + hist_len]), d_seq0_len);
      //     }
      //   }
      // }

      memcpy(out, &in[0], sizeof(gr_complex)*noutput_items);
      // Tell runtime system how many output items we produced.
      return noutput_items;
    }


    // DEBUG
    std::string frame_sync_cc_impl::get_crosscorr0_peaks() {
      return d_crosscorr0->peaks_to_json();
    }

    std::string frame_sync_cc_impl::get_peaks_json() {
        using namespace rapidjson;

        rapidjson::StringBuffer s;
        Document d;

        rapidjson::PrettyWriter<rapidjson::StringBuffer> w(s);
        std::string ret_js;

        d_tracker->to_json(w);

        std::string st = s.GetString();
        d.Parse(st.c_str());
        return st;
    }

    // std::string frame_sync_cc_impl::get_hypotheses() {
    //   using namespace rapidjson;

    //   rapidjson::StringBuffer s;
    //   Document d;

    //   rapidjson::PrettyWriter<rapidjson::StringBuffer> w(s);
    //   std::vector<std::string> peak_strs(hypothesis_vec.size());

    //   w.StartArray();
    //   for(std::vector<detection_instance>::iterator it = hypothesis_vec.begin(); it != hypothesis_vec.end(); ++it) {
    //     w.StartObject();
    //     w.String("idx");
    //     w.Int(it->idx);
    //     w.String("corr_val");
    //     w.Double(it->corr_val);
    //     w.String("cfo");
    //     w.Double(it->cfo);
    //     w.EndObject();
    //   }
    //   w.EndArray();

    //   std::string st = s.GetString();
    //   d.Parse(st.c_str());
    //   return st;
    // }

  } /* namespace specmonitor */
} /* namespace gr */

