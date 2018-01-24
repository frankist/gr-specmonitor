/* -*- c++ -*- */
/* 
 * Copyright 2018 <+YOU OR YOUR COMPANY+>.
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
#include <iostream>
#include "foo_random_burst_shaper_cc_impl.h"

#define dout d_debug && std::cout

namespace gr {
  namespace specmonitor {

    foo_random_burst_shaper_cc::sptr
    foo_random_burst_shaper_cc::make(bool debug, bool delay, double delay_sec,
                                     std::string dist, const std::vector<float>& params,
                                     int pre_padding, const std::vector<float>& freq_offset_values)
    {
      return gnuradio::get_initial_sptr
        (new foo_random_burst_shaper_cc_impl(debug, delay,
                                             delay_sec, dist, params,
                                             pre_padding, freq_offset_values));
    }

    /*
     * The private constructor
     */
    foo_random_burst_shaper_cc_impl::foo_random_burst_shaper_cc_impl(bool debug,
                                                                     bool delay,
                                                                     double delay_sec,
                                                                     std::string dist,
                                                                     const std::vector<float>& params,
                                                                     int pre_padding,
                                                                     const std::vector<float>& freq_offset_values)
      : gr::tagged_stream_block("foo_random_burst_shaper_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
                                gr::io_signature::make(1, 1, sizeof(gr_complex)), "packet_len"),
      d_debug(debug),
      d_pad_front(pre_padding),
      d_pad(0),
      d_eob(false),
      d_delay(delay),
      d_delay_sec(delay_sec),
      d_distname(dist),
      d_params(params)
    {
      d_pad_dist = distribution_factory(dist, params);
      d_pad_tail = d_pad_dist->gen();
      set_tag_propagation_policy(block::TPP_DONT);
    }

    /*
     * Our virtual destructor.
     */
    foo_random_burst_shaper_cc_impl::~foo_random_burst_shaper_cc_impl() {
      delete d_pad_dist;
    }

    int foo_random_burst_shaper_cc_impl::calculate_output_stream_length(const gr_vector_int &ninput_items) {
      return ninput_items[0] + d_pad_front + d_pad_tail;
    }

    int foo_random_burst_shaper_cc_impl::work(int noutput_items,
             gr_vector_int &ninput_items,
             gr_vector_const_void_star &input_items,
             gr_vector_void_star &output_items) {

      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      std::memset(out, 0x00, sizeof(gr_complex) * (ninput_items[0] + d_pad_front + d_pad_tail));
      std::memcpy(out + d_pad_front, in, sizeof(gr_complex) * ninput_items[0]);
      int produced = ninput_items[0] + d_pad_front + d_pad_tail;
      const pmt::pmt_t src = pmt::string_to_symbol(alias());
      d_pad_tail = d_pad_dist->gen();

#ifdef FOO_UHD
      if(d_delay) {
        static const pmt::pmt_t time_key = pmt::string_to_symbol("tx_time");
        struct timeval t;
        gettimeofday(&t, NULL);
        uhd::time_spec_t now = uhd::time_spec_t(t.tv_sec + t.tv_usec / 1000000.0)
          + uhd::time_spec_t(d_delay_sec);

        const pmt::pmt_t time_value = pmt::make_tuple(
                                                      pmt::from_uint64(now.get_full_secs()),
                                                      pmt::from_double(now.get_frac_secs())
                                                      );
        add_item_tag(0, nitems_written(0), time_key, time_value, src);
      }
#endif
      std::vector<gr::tag_t> tags;
      get_tags_in_range(tags, 0, nitems_read(0), nitems_read(0) + ninput_items[0]);
      for (size_t i = 0; i < tags.size(); i++) {
        add_item_tag(0, nitems_written(0),
                     tags[i].key,
                     tags[i].value);
      }

      return produced;
    }

    //   int ninput = ninput_items[0];
    //   int noutput = noutput_items;

    //   // pad zeros
    //   if(d_pad) {
    //     int n = std::min(d_pad, noutput);
    //     std::memset(out, 0, n * sizeof(gr_complex));
    //     d_pad -= n;

    //     dout << "padded zeros: " << n << std::endl;

    //     // add end of burst tag
    //     if(!d_pad && d_eob) {
    //       d_eob = false;
    //       add_eob(nitems_written(0) + n - 1);
    //     }
    //     return n;
    //   }

    //   // search for tags
    //   const uint64_t nread = this->nitems_read(0);
    //   std::vector<gr::tag_t> tags;
    //   get_tags_in_range(tags, 0, nread, nread + ninput);
    //   std::sort(tags.begin(), tags.end(), tag_t::offset_compare);

    //   uint64_t n = std::min(ninput, noutput);

    //   if(tags.size()) {
    //     tag_t t = tags[0];

    //     dout << "found tag: " << pmt::symbol_to_string(t.key) << std::endl;

    //     uint64_t read = nitems_read(0);
    //     if(t.offset != read) {
    //       dout << "tag does not start at current offset" << std::endl;
    //       n = std::min(n, t.offset - read);

    //     }
    //     else {
    //       if(pmt::equal(t.key, pmt::mp("tx_sob"))) {
    //         dout << "tx_sob tag" << std::endl;
    //         add_sob(nitems_written(0));
    //         d_pad = d_pad_front;
    //         remove_item_tag(0, t);
    //         return 0;


    //       }
    //       else if(pmt::equal(t.key, pmt::mp("tx_eob"))) {
    //         dout << "tx_eob tag" << std::endl;
    //         d_pad = d_pad_tail;
    //         // reset d_pad_tail
    //         d_pad_tail = d_pad_dist->gen();
    //         d_eob = true;
    //         if(n) {

    //           if(!d_pad) {
    //             add_eob(nitems_written(0));
    //             d_eob = false;
    //           }
    //           memcpy(out, in, sizeof(gr_complex));
    //           consume(0, 1);
    //           return 1;
    //         }
    //         return 0;

    //       }
    //       else {
    //         dout << "unknown tag" << std::endl;
    //         if(tags.size() > 1) {
    //           n = std::min(n, tags[1].offset - read);
    //         }
    //       }
    //     }
    //   }

    //   dout << "copying : " << n << std::endl;

    //   std::memcpy(out, in, n * sizeof(gr_complex));
    //   consume(0,n);
    //   return n;
    // }

//     void foo_random_burst_shaper_cc_impl::add_sob(uint64_t item) {
//       dout << "PACKET PAD: insert sob at: " << item << std::endl;

//       static const pmt::pmt_t sob_key = pmt::string_to_symbol("tx_sob");
//       static const pmt::pmt_t value = pmt::PMT_T;
//       static const pmt::pmt_t srcid = pmt::string_to_symbol(alias());
//       add_item_tag(0, item, sob_key, value, srcid);

// #ifdef FOO_UHD
//       if(d_delay) {
//         static const pmt::pmt_t time_key = pmt::string_to_symbol("tx_time");
//         struct timeval t;
//         gettimeofday(&t, NULL);
//         uhd::time_spec_t now = uhd::time_spec_t(t.tv_sec + t.tv_usec / 1000000.0)
//           + uhd::time_spec_t(d_delay_sec);

//         const pmt::pmt_t time_value = pmt::make_tuple(
//                                                       pmt::from_uint64(now.get_full_secs()),
//                                                       pmt::from_double(now.get_frac_secs())
//                                                       );
//         add_item_tag(0, item, time_key, time_value, srcid);
//       }
// #endif
//     }

//     void foo_random_burst_shaper_cc_impl::add_eob(uint64_t item) {
//       dout << "PACKET PAD: insert eob at: " << item << std::endl;

//       static const pmt::pmt_t eob_key = pmt::string_to_symbol("tx_eob");
//       static const pmt::pmt_t value = pmt::PMT_T;
//       static const pmt::pmt_t srcid = pmt::string_to_symbol(alias());
//       add_item_tag(0, item, eob_key, value, srcid);
//     }
  } /* namespace specmonitor */
} /* namespace gr */

