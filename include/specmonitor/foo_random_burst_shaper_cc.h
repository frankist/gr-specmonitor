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


#ifndef INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_H
#define INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_H

#include <specmonitor/api.h>
#include <gnuradio/tagged_stream_block.h>

namespace gr {
  namespace specmonitor {

    /*!
     * \brief <+description of block+>
     * \ingroup specmonitor
     *
     */
    class SPECMONITOR_API foo_random_burst_shaper_cc : virtual public gr::tagged_stream_block
    {
     public:
      typedef boost::shared_ptr<foo_random_burst_shaper_cc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of specmonitor::foo_random_burst_shaper_cc.
       *
       * To avoid accidental use of raw pointers, specmonitor::foo_random_burst_shaper_cc's
       * constructor is in a private implementation
       * class. specmonitor::foo_random_burst_shaper_cc::make is the public interface for
       * creating new instances.
       */
      static sptr make(bool debug, bool delay, double delay_sec, std::string dist, const std::vector<float>& params, int pre_padding, const std::vector<float>& freq_offset_values);
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FOO_RANDOM_BURST_SHAPER_CC_H */

