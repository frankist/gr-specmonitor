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


#ifndef INCLUDED_SPECMONITOR_FRAMER_C_H
#define INCLUDED_SPECMONITOR_FRAMER_C_H

#include <specmonitor/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace specmonitor {

    /*!
     * \brief <+description of block+>
     * \ingroup specmonitor
     *
     */
    class SPECMONITOR_API framer_c : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<framer_c> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of specmonitor::framer_c.
       *
       * To avoid accidental use of raw pointers, specmonitor::framer_c's
       * constructor is in a private implementation
       * class. specmonitor::framer_c::make is the public interface for
       * creating new instances.
       */
      static sptr make(double sample_rate, double frame_duration, std::vector<gr_complex> preamble_seq);
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FRAMER_C_H */

