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

#ifndef INCLUDED_SPECMONITOR_FRAME_SYNC_CC_IMPL_H
#define INCLUDED_SPECMONITOR_FRAME_SYNC_CC_IMPL_H

#include <specmonitor/frame_sync_cc.h>
#include <gnuradio/filter/fft_filter.h>
#include "utils/digital/moving_average.h"
#include "crosscorr_detector_cc.h"

namespace gr {
  namespace specmonitor {

    class frame_sync_cc_impl : public frame_sync_cc
    {
     private:
      std::vector<std::vector<gr_complex> > d_preamble_seq;
      std::vector<int> d_n_repeats;
      float d_thres;

      float d_awgn;
      short d_state;

      crosscorr_detector_cc* d_crosscorr0;

     public:
      frame_sync_cc_impl(const std::vector<std::vector<gr_complex> >& preamble_seq, const std::vector<int>& n_repeats, float thres);
      ~frame_sync_cc_impl();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);

      // debug internal variables
      std::vector<gr_complex> get_crosscorr0(int N) {
        return std::vector<gr_complex>(&d_crosscorr0->d_corr[0],&d_crosscorr0->d_corr[N]);
      }
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FRAME_SYNC_CC_IMPL_H */

