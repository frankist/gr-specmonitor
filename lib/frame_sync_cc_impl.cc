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

namespace gr {
  namespace specmonitor {

    frame_sync_cc::sptr
    frame_sync_cc::make(const std::vector<std::vector<gr_complex> >& preamble_seq,
                        const std::vector<int>& n_repeats, float thres)
    {
      return gnuradio::get_initial_sptr
        (new frame_sync_cc_impl(preamble_seq, n_repeats, thres));
    }

    /*
     * The private constructor
     */
    frame_sync_cc_impl::frame_sync_cc_impl(const std::vector<std::vector<gr_complex> >& preamble_seq,
                                           const std::vector<int>& n_repeats, float thres)
      : gr::sync_block("frame_sync_cc",
                       gr::io_signature::make(1, 1, sizeof(gr_complex)),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
        d_preamble_seq(preamble_seq), d_n_repeats(n_repeats), d_thres(thres),
        d_awgn(0), d_state(0)
    {
      // In order to easily support the optional second output,
      // don't deal with an unbounded max number of output items.
      // For the common case of not using the optional second output,
      // this ensures we optimally call the volk routines.
      const size_t nitems = 24*1024;
      set_max_noutput_items(nitems);

      d_crosscorr0 = new crosscorr_detector_cc(d_preamble_seq[0], d_n_repeats[0], nitems, d_thres);

      set_history(d_n_repeats[0]*preamble_seq[0].size()+1);
    }

    /*
     * Our virtual destructor.
     */
    frame_sync_cc_impl::~frame_sync_cc_impl()
    {
      delete d_crosscorr0;
    }

    int
    frame_sync_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      // Our correlation filter length
      unsigned int hist_len = history() - 1;

      d_crosscorr0->work(in, noutput_items, hist_len, nitems_read(0), 1);

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

  } /* namespace specmonitor */
} /* namespace gr */

