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
#include "framer_snr_est_cc_impl.h"

namespace gr {
  namespace specmonitor {

    framer_snr_estimator::sptr
    framer_snr_estimator::make(int num_estim_samples)
    {
      return gnuradio::get_initial_sptr
        (new framer_snr_est_cc_impl(num_estim_samples));
    }

    /*
     * The private constructor
     */
    framer_snr_est_cc_impl::framer_snr_est_cc_impl(int num_estim_samples)
      : gr::sync_block("framer_snr_estimator",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
        d_src_id(pmt::intern(alias()))
    {
      d_num_estim_samples = num_estim_samples;

      d_mag2_diff = -1.0;
      d_mag2_est = -1.0;
      d_snr_estim = 1.0;
      estim_samples_counter = 0;
    }

    /*
     * Our virtual destructor.
     */
    framer_snr_est_cc_impl::~framer_snr_est_cc_impl()
    {
    }

    float framer_snr_est_cc_impl::SNRdB()
    {
      return 10*log10(d_snr_estim);
    }

    int
    framer_snr_est_cc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex*) input_items[0];
      gr_complex *out = (gr_complex*) output_items[0];

      std::vector<tag_t> tags;
      get_tags_in_range(tags, 0, nitems_read(0),
                        nitems_read(0)+noutput_items,
                        pmt::intern("mag2_est"));

      if(tags.size()>0 || estim_samples_counter>0) {
        int tag_idx = 0;
        for(int i = 0; i < noutput_items; i++) {
          if(d_num_estim_samples>0) {
            d_noise_mag2 += std::norm(in[i]);
            if(--d_num_estim_samples==0) {
              d_noise_mag2 /= d_num_estim_samples;
              d_snr_estim = d_mag2_est / d_noise_mag2;
              add_item_tag(0, nitems_written(0) + index, pmt::intern("snr_estim"), pmt::from_double(d_snr_estim), d_src_id);
              add_item_tag(0, nitems_written(0) + index, pmt::intern("noise_pwr"), pmt::from_double(d_noise_mag2), d_src_id);
            }
          }
          else if(tags[tag_idx].offset-nitems_read(0) == (size_t)i) {
            estim_samples_counter = d_num_estim_samples;
            float new_mag2_est = (float)pmt::to_double(tags[tag_idx++].value);
            d_mag2_diff = (d_mag2_est < 0) ? 0 : new_mag2_est - d_mag2_est;
            d_mag2_est = new_mag2_est;
          }
      }

      memcpy(out, &in[0], sizeof(gr_complex)*noutput_items);

      return noutput_items;
    }

  } /* namespace specmonitor */
} /* namespace gr */

