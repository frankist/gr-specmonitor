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

#include <boost/format.hpp>
#include <gnuradio/io_signature.h>
#include <volk/volk.h>
#include <limits>
#include "random_burst_shaper_cc_impl.h"
#include "utils/digital/channel.h"

namespace gr {
  namespace specmonitor {

    random_burst_shaper_cc::sptr
    random_burst_shaper_cc::make(std::string dist,
                                 const std::vector<float>& params,
                                 int pre_padding,
                                 const std::vector<float>& freq_offset_values,
                                 const std::string &length_tag_name)
    {
      return gnuradio::get_initial_sptr
        (new random_burst_shaper_cc_impl(dist, params, pre_padding, freq_offset_values, length_tag_name));
    }

    /*
     * The private constructor
     */
    random_burst_shaper_cc_impl::random_burst_shaper_cc_impl(std::string dist,
                                                             const std::vector<float>& params,
                                                             int pre_padding,
                                                             const std::vector<float>& freq_offset_values,
                                                             const std::string &length_tag_name)
      : gr::block("random_burst_shaper_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
                  gr::io_signature::make(1, 1, sizeof(gr_complex))),
      d_distname(dist),
      d_params(params),
      d_nprepad(pre_padding),
      d_freq_offset_values(freq_offset_values),
      d_dist(NULL),
      d_freq_dist(0,freq_offset_values.size()-1),
      d_length_tag_key(pmt::string_to_symbol(length_tag_name)),
      d_ncopy(0),
      d_limit(0),
      d_index(0),
      d_length_tag_offset(0),
      d_finished(false),
      d_state(STATE_WAIT)
    {
      int param_idx = 0;
      if(d_distname=="poisson") {
        switch(d_params.size()) {
        case 1:
          d_dist = new PoissonDist(d_params[param_idx++]);
          break;
        case 2:
          d_dist = new PoissonDist(d_params[param_idx++],d_params[param_idx++]);
          break;
        case 3:
          d_dist = new PoissonDist(d_params[param_idx++],d_params[param_idx++],d_params[param_idx++]);
          break;
        default:
          std::stringstream ss;
          ss << "Invalid number of parameters (";
          ss << d_params.size();
          ss << ") for the distribution";
          throw std::invalid_argument(ss.str());
        }
      }
      else if(d_distname=="uniform") {
        if(d_params.size()!=2)
          throw std::invalid_argument("Invalid number of parameters for the distribution");
        d_dist = new UniformIntDist(d_params[0],d_params[1]);
        param_idx+=2;
      }
      else {
        std::string errmsg = "I do not recognise the distribution " + d_distname;
        throw std::invalid_argument(errmsg);
      }

      update_npostpad();
      set_tag_propagation_policy(TPP_DONT);
    }

    /*
     * Our virtual destructor.
     */
    random_burst_shaper_cc_impl::~random_burst_shaper_cc_impl()
    {
      std::cout << "Going to auto destruct" << std::endl;
      if(d_dist!=NULL)
        delete d_dist;
      d_dist = NULL;
    }

    void
    random_burst_shaper_cc_impl::forecast (int noutput_items,
                                           gr_vector_int &ninput_items_required)
    {
      if(STATE_POSTPAD) {
        ninput_items_required[0] = 0;
      }
      else {
        ninput_items_required[0] = noutput_items;
      }
    }

    int
    random_burst_shaper_cc_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const gr_complex *in = reinterpret_cast<const gr_complex *>(input_items[0]);
      gr_complex *out = reinterpret_cast<gr_complex *>(output_items[0]);

      int nwritten = 0;
      int nread = 0;
      int nspace = 0;
      int nskip = 0;
      int curr_tag_index = 0;

      std::vector<tag_t> length_tags;
      get_tags_in_window(length_tags, 0, 0, ninput_items[0], d_length_tag_key);
      std::sort(length_tags.rbegin(), length_tags.rend(), tag_t::offset_compare);

      while(nwritten < noutput_items) {
        // Only check the nread condition if we are actually reading
        // from the input stream.
        if(d_state != STATE_POSTPAD) {
          if(nread >= ninput_items[0]) {
            break;
          }
        }

        if(d_finished) {
          d_finished = false;
          break;
        }

        nspace = noutput_items - nwritten;
        switch(d_state) {
        case(STATE_WAIT):
          if(!length_tags.empty()) {
            d_length_tag_offset = length_tags.back().offset;
            curr_tag_index = (int)(d_length_tag_offset - nitems_read(0));
            d_ncopy = pmt::to_long(length_tags.back().value);
            length_tags.pop_back();
            nskip = curr_tag_index - nread;
            add_length_tag(nwritten);
            propagate_tags(curr_tag_index, nwritten, 1, false);
            enter_prepad();
          }
          else {
            nskip = ninput_items[0] - nread;
          }
          if(nskip > 0) {
            GR_LOG_WARN(d_logger,
                        boost::format("Dropping %1% samples") %
                        nskip);
            nread += nskip;
            in += nskip;
          }
          break;

        case(STATE_PREPAD):
          write_padding(out, nwritten, nspace);
          if(d_index == d_limit)
            enter_copy();
          break;

        case(STATE_COPY):
          copy_items(out, in, nwritten, nread, nspace);
          if(d_index == d_limit)
            enter_postpad();
          break;

        case(STATE_POSTPAD):
          write_padding(out, nwritten, nspace);
          if(d_index == d_limit)
            enter_wait();
          break;

        default:
          throw std::runtime_error("random_burst_shaper_cc: invalid state");
        }
      }

      consume_each(nread);

      return nwritten;
    }

    void random_burst_shaper_cc_impl::update_npostpad() {
      d_npostpad = d_dist->gen();
      // std::cout << "New postpad: " << d_npostpad << "\n";
    }

    void random_burst_shaper_cc_impl::write_padding(gr_complex *&dst, int &nwritten, int nspace)
    {
        int nprocess = std::min(d_limit - d_index, nspace);
        std::memset(dst, 0x00, nprocess * sizeof(gr_complex));
        dst += nprocess;
        nwritten += nprocess;
        d_index += nprocess;
    }

    void random_burst_shaper_cc_impl::copy_items(gr_complex *&dst,
                                                 const gr_complex *&src,
                                                 int &nwritten,
                                                 int &nread,
                                                 int nspace)
    {
        int nprocess = std::min(d_limit - d_index, nspace);
        propagate_tags(nread, nwritten, nprocess);
        utils::frequency_shift<gr_complex>(dst,src,d_freq_offset_values[d_freq_dist(d_rng)],nprocess);
        // std::memcpy(dst, src, nprocess * sizeof(gr_complex));
        dst += nprocess;
        nwritten += nprocess;
        src += nprocess;
        nread += nprocess;
        d_index += nprocess;
    }

    void
    random_burst_shaper_cc_impl::add_length_tag(int offset)
    {
        add_item_tag(0, nitems_written(0) + offset, d_length_tag_key,
                     pmt::from_long(d_ncopy + d_nprepad +
                                    d_npostpad),
                     pmt::string_to_symbol(name()));
    }

    void random_burst_shaper_cc_impl::propagate_tags(int in_offset,
                                                     int out_offset,
                                                     int count,
                                                     bool skip)
    {
      uint64_t abs_start = nitems_read(0) + in_offset;
      uint64_t abs_end = abs_start + count;
      uint64_t abs_offset = nitems_written(0) + out_offset;
      tag_t temp_tag;

      std::vector<tag_t> tags;
      std::vector<tag_t>::iterator it;

      get_tags_in_range(tags, 0, abs_start, abs_end);

      for(it = tags.begin(); it != tags.end(); it++) {
        if(!pmt::equal(it->key, d_length_tag_key)) {
          if(skip && (it->offset == d_length_tag_offset))
            continue;
          temp_tag = *it;
          temp_tag.offset = abs_offset + it->offset - abs_start;
          add_item_tag(0, temp_tag);
        }
      }
    }

    void random_burst_shaper_cc_impl::enter_wait()
    {
      d_finished = true;
      d_index = 0;
      d_state = STATE_WAIT;
      update_npostpad();
    }

    void random_burst_shaper_cc_impl::enter_prepad()
    {
      d_limit = d_nprepad;
      d_index = 0;
      d_state = STATE_PREPAD;
    }

    void random_burst_shaper_cc_impl::enter_copy()
    {
      d_limit = d_ncopy;// - std::min((size_t)((d_ncopy/2)*2),0);
      d_index = 0;
      d_state = STATE_COPY;
    }

    void random_burst_shaper_cc_impl::enter_postpad()
    {
      d_limit = d_npostpad;
      d_index = 0;
      d_state = STATE_POSTPAD;
    }
  } /* namespace specmonitor */
} /* namespace gr */

