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

// NOTE: This is based on the padder block in https://github.com/bastibl/gr-foo
//       I just needed it to support more randomized padding

#ifndef INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_IMPL_H
#define INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_IMPL_H

#include <specmonitor/foo_random_burst_shaper_cc.h>
#include "specmonitor_random.h"

namespace gr {
  namespace specmonitor {

    class foo_random_burst_shaper_cc_impl : public foo_random_burst_shaper_cc
    {
     private:
      int calculate_output_stream_length(const gr_vector_int &ninput_items);
			// void add_eob(uint64_t item);
			// void add_sob(uint64_t item);

      // arguments
			bool d_debug;
			bool d_delay;
			double d_delay_sec;
      std::string d_distname;
      std::vector<float> d_params;
			int d_pad_front;
			int d_pad_tail;
      // const int d_nprepad;
      // const std::vector<float> d_freq_offset_values;

      // internal
			int d_pad;
			bool d_eob;
      DistAbstract* d_pad_dist;

     public:
      foo_random_burst_shaper_cc_impl(bool debug, bool delay, double delay_sec, std::string dist, const std::vector<float>& params, int pre_padding, const std::vector<float>& freq_offset_values);
      ~foo_random_burst_shaper_cc_impl();

      int work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_IMPL_H */

