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

#ifndef INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_IMPL_H
#define INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_IMPL_H

#include <specmonitor/random_burst_shaper_cc.h>
#include <boost/random.hpp>
#include <ctime>

namespace gr {
  namespace specmonitor {
    class DistAbstract;

    class random_burst_shaper_cc_impl : public random_burst_shaper_cc
    {
    protected:
      enum state_t {STATE_WAIT, STATE_PREPAD, STATE_RAMPUP,
                    STATE_COPY, STATE_RAMPDOWN, STATE_POSTPAD};
     private:
      std::string d_distname;
      std::vector<float> d_params;
      const int d_nprepad;
      const std::vector<float> d_freq_offset_values;

      DistAbstract* d_dist;
      boost::random::mt19937 d_rng;
      boost::random::uniform_int_distribution<> d_freq_dist;
      int d_npostpad;
      const pmt::pmt_t d_length_tag_key;
      int d_ncopy;
      int d_limit;
      int d_index;
      uint64_t d_length_tag_offset;
      bool d_finished;
      state_t d_state;
      int d_cur_freq_offset;
      std::vector<gr_complex> d_buffer;
      float d_phase_init;
      int d_bufnread;
      std::vector<tag_t> d_length_tags;

      void write_padding(gr_complex *dst, int &nwritten, int nspace);
      int copy_items(gr_complex *dst, const gr_complex *src, int &nwritten,
                      int &nread, int nspace, int readspace);
      void add_length_tag(int offset);
      void propagate_tags(int in_offset, int out_offset, int count, bool skip=true);
      void enter_wait();
      void enter_prepad();
      void enter_copy();
      void enter_postpad();
      void update_npostpad();
     public:
      random_burst_shaper_cc_impl(std::string dist,
                                  const std::vector<float>& params,
                                  int pre_padding,
                                  const std::vector<float>& freq_offset_values,
                                  const std::string &length_tag_name);
      ~random_burst_shaper_cc_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);
      int pre_padding() const { return d_nprepad; }
      int post_padding() const { return d_npostpad; }
    };

    struct DistAbstract {
      std::uint32_t seed;
      boost::random::mt19937 rng;
      DistAbstract() : seed(static_cast<std::uint32_t>(std::time(0))), rng(seed)
      {}
      virtual int gen() = 0;
    };

    struct UniformIntDist : public DistAbstract {
      boost::random::uniform_int_distribution<> d_dist;
      UniformIntDist(int left, int right) : d_dist(left,right) {}
      int gen() {
        return d_dist(rng);
      }
    };

    struct PoissonDist : public DistAbstract {
      boost::random::poisson_distribution<> d_dist;
      int d_offset;
      int d_upper_limit;
      PoissonDist(int mean,
                  int offset=0,
                  int upper_limit = std::numeric_limits<int>::max()) :
        d_dist(mean),
        d_offset(offset),
        d_upper_limit(upper_limit) {}
      int gen() {
        return std::min(d_offset+d_dist(rng),d_upper_limit);
      }
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_IMPL_H */

