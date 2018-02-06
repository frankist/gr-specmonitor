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
    random_burst_shaper_cc::make(DynRandom time_dist,
                                 int pre_padding,
                                 const std::vector<float>& freq_offset_values,
                                 const std::string &length_tag_name)
    {
      return gnuradio::get_initial_sptr
        (new random_burst_shaper_cc_impl(time_dist, pre_padding, freq_offset_values, length_tag_name));
    }

    /*
     * The private constructor
     */
    random_burst_shaper_cc_impl::random_burst_shaper_cc_impl(DynRandom time_dist,
                                                             int pre_padding,
                                                             const std::vector<float>& freq_offset_values,
                                                             const std::string &length_tag_name)
      : gr::block("random_burst_shaper_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
                  gr::io_signature::make(1, 1, sizeof(gr_complex))),
      d_nprepad(pre_padding),
      d_freq_offset_values(freq_offset_values),
      // d_dist(NULL),
      // d_dist2(NULL),
      d_freq_dist(0,freq_offset_values.size()-1),
      d_length_tag_key(pmt::string_to_symbol(length_tag_name)),
      d_ncopy(0),
      d_limit(0),
      d_index(0),
      d_length_tag_offset(0),
      d_finished(false),
      d_state(STATE_WAIT),
      d_phase_init(0),
      d_bufnread(0),
      d_rng(static_cast<unsigned int>(std::time(0)))
    {
      int param_idx = 0;
      d_dist = new DynRandom(time_dist);

      d_cur_freq_offset = d_freq_dist(d_rng);

      update_npostpad();
      set_tag_propagation_policy(TPP_DONT);
      std::cout << "Exit constructor of burst shaper" << std::endl;
    }

    /*
     * Our virtual destructor.
     */
    random_burst_shaper_cc_impl::~random_burst_shaper_cc_impl()
    {
      std::cout << "burst destructor called!" << std::endl;
      if(d_dist!=NULL)
        delete d_dist;
      d_dist = NULL;
    }

    void
    random_burst_shaper_cc_impl::forecast (int noutput_items,
                                           gr_vector_int &ninput_items_required)
    {
      if(d_state==STATE_POSTPAD) {
        ninput_items_required[0] = 0;
      }
      else {
        if(d_state==STATE_PREPAD or d_state==STATE_WAIT) {
          ninput_items_required[0] = std::max(noutput_items-d_bufnread,1);
        }
        else
          ninput_items_required[0] = std::max(noutput_items-d_bufnread,0);
      }
      // std::cout << "FORECAST CALLED: " << d_state << "," << ninput_items_required[0] << std::endl;
    }

    int
    random_burst_shaper_cc_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const gr_complex *xin = reinterpret_cast<const gr_complex *>(input_items[0]);
      gr_complex *xout = reinterpret_cast<gr_complex *>(output_items[0]);

      int nwritten = 0;
      int nread = 0;
      int nspace = 0;
      int nskip = 0;
      int curr_tag_index = 0;

      get_tags_in_window(d_length_tags, 0, 0, ninput_items[0], d_length_tag_key);
      std::sort(d_length_tags.rbegin(), d_length_tags.rend(), tag_t::offset_compare);

      // std::cout << "I am at the start. Number of tags: " << d_length_tags.size()
      //           << ", Number of input samples: " << ninput_items[0]
      //           << ", Number of output samples: " << noutput_items
      //           << ",state:" << d_state << ",is_WAIT:" << (d_state==STATE_WAIT)
      //           << ",is_POSTPAD:" << (d_state==STATE_POSTPAD)
      //           << ",d_index/d_total:" << d_index << "/" << d_limit << std::endl;

      while(nwritten < noutput_items) {
        // Only check the nread condition if we are actually reading
        // from the input stream.
        if(d_state != STATE_POSTPAD && d_state != STATE_PREPAD) {
          if(nread >= ninput_items[0]) {
            break;
          }
        }

        // if(d_finished) {
        //   d_finished = false;
        //   break;
        // }

        nspace = noutput_items - nwritten;
        switch(d_state) {
        case(STATE_WAIT):
          if(!d_length_tags.empty()) {
            d_length_tag_offset = d_length_tags.back().offset;
            curr_tag_index = (int)(d_length_tag_offset - nitems_read(0));
            d_ncopy = pmt::to_long(d_length_tags.back().value);
            d_length_tags.pop_back();
            nskip = curr_tag_index - nread;
            add_length_tag(nwritten);
            propagate_tags(curr_tag_index, nwritten, 1, false);
            enter_prepad();
          }
          else {
            nskip = ninput_items[0] - nread;
            // std::cout << "I am here! seed: " << d_dist->seed << ",nread:" << nread << ",nskip:" << nskip << std::endl;
          }
          if(nskip > 0) {
            GR_LOG_WARN(d_logger,
                        boost::format("Dropping %1% samples") %
                        nskip);
            nread += nskip;
            // exit(-1);
          }
          break;

        case(STATE_PREPAD):
          write_padding(&xout[nwritten], nwritten, nspace);
          if(d_index == d_limit) {
            enter_copy();
            d_burst_list.push_back(nitems_written(0)+nwritten);
          }
          break;

        case(STATE_COPY):
          // if(d_buffer.size()>0){
          //   int ncopied = copy_items(&xout[nwritten],
          //                            &d_buffer[0], nwritten,
          //                            d_bufnread, nspace, d_buffer.size());
          //   d_buffer.erase(d_buffer.begin(),d_buffer.begin()+ncopied);
          // }
          // else
          copy_items(&xout[nwritten], &xin[nread], nwritten, nread, nspace, ninput_items[0]-nread);
          if(d_index == d_limit)
            enter_postpad();
          break;

        case(STATE_POSTPAD):
          write_padding(&xout[nwritten], nwritten, nspace);
          if(d_index == d_limit)
            enter_wait();
          break;

        default:
          throw std::runtime_error("random_burst_shaper_cc: invalid state");
        }
      }

      // if(ninput_items[0]>nread) {
      //   d_buffer.resize(ninput_items[0]-nread);
      //   std::copy(&xin[nread], &xin[ninput_items[0]], &d_buffer[0]);
      //   d_bufnread = -d_buffer.size();
      // }

      d_bufnread = ninput_items[0]-nread;
      // std::cout << "I am out:" << nread << "," << ninput_items[0]
      //           << ", this is my buffer size: " << d_bufnread << std::endl;
      consume_each(nread);

      return nwritten;
    }

    void random_burst_shaper_cc_impl::update_npostpad()
    {
      d_npostpad = d_dist->generate();
    }

    void random_burst_shaper_cc_impl::write_padding(gr_complex *dst, int &nwritten, int nspace)
    {
        int nprocess = std::min(d_limit - d_index, nspace);
        std::memset(dst, 0x00, nprocess * sizeof(gr_complex));
        nwritten += nprocess;
        d_index += nprocess;
    }

    int random_burst_shaper_cc_impl::copy_items(gr_complex *dst,
                                                 const gr_complex *src,
                                                 int &nwritten,
                                                 int &nread,
                                                 int writespace,
                                                 int readspace)
    {
      float phase_init = (d_index==0) ? 0 : d_phase_init;
      int nprocess = std::min(d_limit - d_index, std::min(writespace,readspace));
      propagate_tags(nread, nwritten, nprocess);
      d_phase_init = utils::frequency_shift<gr_complex>(dst,src,d_freq_offset_values[d_cur_freq_offset],nprocess, phase_init);
      // std::memcpy(dst, src, nprocess * sizeof(gr_complex));
      nwritten += nprocess;
      nread += nprocess;
      d_index += nprocess;

      return nprocess;
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
      //d_finished = true;
      d_index = 0;
      d_state = STATE_WAIT;
      update_npostpad();
      d_cur_freq_offset = d_freq_dist(d_rng);
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

