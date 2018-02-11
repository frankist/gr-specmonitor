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


#ifndef INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_H
#define INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_H

#include <specmonitor/api.h>
#include <gnuradio/block.h>
#include "DynRandom.h"

namespace gr {
  namespace specmonitor {
    class SPECMONITOR_API DynRandom; // NOTE: I need to define API for swig to find it
    /*!
     * \brief <+description of block+>
     * \ingroup specmonitor
     *
     */
    class SPECMONITOR_API random_burst_shaper_cc : virtual public gr::block
    {
     public:
      typedef boost::shared_ptr<random_burst_shaper_cc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of specmonitor::random_burst_shaper_cc.
       *
       * To avoid accidental use of raw pointers, specmonitor::random_burst_shaper_cc's
       * constructor is in a private implementation
       * class. specmonitor::random_burst_shaper_cc::make is the public interface for
       * creating new instances.
       */
      static sptr make(DynRandom time_dist,
                       int pre_padding = 0,
                       const std::vector<float>& freq_offset_values = std::vector<float>(1,0),
                       const std::string &length_tag_name = "packet_len");
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_RANDOM_BURST_SHAPER_CC_H */

