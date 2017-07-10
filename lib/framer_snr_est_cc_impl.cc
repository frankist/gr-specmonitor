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

    framer_snr_est_cc::sptr
    framer_snr_est_cc::make(int num_estim_samples, int seq_length)
    {
      return gnuradio::get_initial_sptr
        (new framer_snr_est_cc_impl(num_estim_samples, seq_length));
    }

    /*
     * The private constructor
     */
    framer_snr_est_cc_impl::framer_snr_est_cc_impl(int num_estim_samples, int seq_length)
      : gr::sync_block("framer_snr_est_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
        d_src_id(pmt::intern(alias()))
    {
      d_num_estim_samples = num_estim_samples;
      d_seq_length = seq_length;

      d_mag2_diff = -1.0;
      d_mag2_est = -1.0;
      d_snr_estim = -1.0;
      d_snr_estim_sum = 0.0;
      d_snr_estim_count = 0;
      d_noise_mag2 = 0.0;
      d_max_counter = d_num_estim_samples + d_seq_length;
      d_estim_samples_counter = d_max_counter;
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

    float framer_snr_est_cc_impl::SNRdB_mean()
    {
      return (d_snr_estim_count==0) ? -1.0 : 10*log10(d_snr_estim_sum/d_snr_estim_count);
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

      if(tags.size()>0 || d_estim_samples_counter<d_max_counter) {
        // std::cout << "Number of tags is: " << tags.size() << std::endl;
        int tag_idx = 0;
        for(int i = 0; i < noutput_items; i++) {
          if(d_estim_samples_counter<d_max_counter) {
            if(d_estim_samples_counter>=d_seq_length)
              d_noise_mag2 += std::norm(in[i]);
            if(++d_estim_samples_counter==d_max_counter) {
              // std::cout << "Finished computing the SNR at " << i << std::endl;
              d_noise_mag2 /= d_num_estim_samples;
              d_snr_estim = (d_mag2_est-d_noise_mag2) / d_noise_mag2;
              d_snr_estim_sum += d_snr_estim;
              d_snr_estim_count++;
              add_item_tag(0, d_tag_offset, pmt::intern("snr_estim"), pmt::from_double(d_snr_estim), d_src_id);
              add_item_tag(0, d_tag_offset, pmt::intern("noise_pwr"), pmt::from_double(d_noise_mag2), d_src_id);
            }
          }
          else if(tags[tag_idx].offset-nitems_read(0) == (size_t)i) {
            d_estim_samples_counter = 0;
            float new_mag2_est = (float)pmt::to_double(tags[tag_idx].value);
            d_mag2_diff = (d_mag2_est < 0) ? 0 : new_mag2_est - d_mag2_est;
            d_mag2_est = new_mag2_est;
            d_tag_offset = tags[tag_idx].offset;
            // std::cout << "Intercepted tag at " << d_tag_offset << ", " << i << std::endl;
            if(tag_idx++>=tags.size())
              break;
          }
        }
      }

      memcpy(out, &in[0], sizeof(gr_complex)*noutput_items);

      return noutput_items;
    }

  } /* namespace specmonitor */
} /* namespace gr */

