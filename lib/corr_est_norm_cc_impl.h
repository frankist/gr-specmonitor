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

#ifndef INCLUDED_SPECMONITOR_CORR_EST_NORM_CC_IMPL_H
#define INCLUDED_SPECMONITOR_CORR_EST_NORM_CC_IMPL_H

#include <specmonitor/corr_est_norm_cc.h>
#include <gnuradio/filter/fft_filter.h>

namespace gr {
  namespace specmonitor {

    class corr_est_norm_cc_impl : public corr_est_norm_cc
    {
     private:
      pmt::pmt_t d_src_id;
      std::vector<gr_complex> d_symbols;
      float d_sps;
      unsigned int d_mark_delay, d_stashed_mark_delay;
      float d_thresh, d_stashed_threshold;
      gr::filter::kernel::fft_filter_ccc *d_filter;
      gr::filter::kernel::fft_filter_fff *d_filter2;

      gr_complex *d_corr;
      float *d_corr_mag;
      float *d_in_mag2;
      float *d_mavg_mag2;
      float *d_corr_mag_norm;
      // std::vector<float> d_corr_mag_norm;

      float d_scale;
      float d_pfa; // probability of false alarm

      void _set_mark_delay(unsigned int mark_delay);
      void _set_threshold(float threshold);

     public:
      corr_est_norm_cc_impl(const std::vector<gr_complex> &symbols,
                            float sps, unsigned int mark_delay,
                            float threshold=0.9);
      ~corr_est_norm_cc_impl();

      std::vector<gr_complex> symbols() const;
      void set_symbols(const std::vector<gr_complex> &symbols);

      unsigned int mark_delay() const;
      void set_mark_delay(unsigned int mark_delay);

      float threshold() const;
      void set_threshold(float threshold);

      int work(int noutput_items,
               gr_vector_const_void_star &input_items,
               gr_vector_void_star &output_items);
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_CORR_EST_NORM_CC_IMPL_H */

