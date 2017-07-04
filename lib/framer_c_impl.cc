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
#include "framer_c_impl.h"

namespace gr {
  namespace specmonitor {

    framer_c::sptr
    framer_c::make(double sample_rate, double frame_duration, std::vector<gr_complex> preamble_seq)
    {
      return gnuradio::get_initial_sptr
        (new framer_c_impl(sample_rate, frame_duration, preamble_seq));
    }

    /*
     * The private constructor
     */
    framer_c_impl::framer_c_impl(double sample_rate, double frame_duration, const std::vector<gr_complex>& preamble_seq)
      : gr::sync_block("framer_c",
              gr::io_signature::make(0, 0, 0),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
              sample_rate_(sample_rate), 
              frame_duration_(frame_duration), 
              preamble_seq_(preamble_seq), 
              idx_(0)
    {
        samples_per_frame_ = (int)round(frame_duration_*sample_rate_);
        std::cout << "Samples per frame: " << samples_per_frame_ << std::endl;
    }

    /*
     * Our virtual destructor.
     */
    framer_c_impl::~framer_c_impl()
    {
    }

    int framer_c_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {   
      gr_complex *out = (gr_complex *) output_items[0];

      // Do <+signal processing+>
      for(int i = 0; i < noutput_items; ++i)
      {
          if(idx_ < preamble_seq_.size())
              out[i] = preamble_seq_[idx_];
          else
              out[i] = 0;
          idx_ = (idx_ + 1) % samples_per_frame_;
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace specmonitor */
} /* namespace gr */

