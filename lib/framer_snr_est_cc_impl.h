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

#ifndef INCLUDED_SPECMONITOR_FRAMER_SNR_EST_CC_IMPL_H
#define INCLUDED_SPECMONITOR_FRAMER_SNR_EST_CC_IMPL_H

#include <specmonitor/framer_snr_est_cc.h>

namespace gr {
  namespace specmonitor {

    class framer_snr_est_cc_impl : public framer_snr_est_cc
    {
     private:
      int d_seq_length;
      int d_num_estim_samples;

      pmt::pmt_t d_src_id;
      float d_snr_estim;
      double d_snr_estim_sum;
      long d_snr_estim_count;
      float d_mag2_est;
      float d_mag2_diff;
      float d_noise_mag2;
      size_t d_tag_offset;
      int d_estim_samples_counter;
      int d_max_counter;

     public:
      framer_snr_est_cc_impl(int num_estim_samples, int seq_length);
      ~framer_snr_est_cc_impl();

      float SNRdB();
      float SNRdB_mean();

      // Where all the action really happens
      int work(int noutput_items,
         gr_vector_const_void_star &input_items,
         gr_vector_void_star &output_items);
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FRAMER_SNR_EST_CC_IMPL_H */

