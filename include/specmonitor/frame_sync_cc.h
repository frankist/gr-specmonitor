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


#ifndef INCLUDED_SPECMONITOR_FRAME_SYNC_CC_H
#define INCLUDED_SPECMONITOR_FRAME_SYNC_CC_H

#include <specmonitor/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace specmonitor {

    /*!
     * \brief <+description of block+>
     * \ingroup specmonitor
     *
     */
    class SPECMONITOR_API frame_sync_cc : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<frame_sync_cc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of specmonitor::frame_sync_cc.
       *
       * To avoid accidental use of raw pointers, specmonitor::frame_sync_cc's
       * constructor is in a private implementation
       * class. specmonitor::frame_sync_cc::make is the public interface for
       * creating new instances.
       */
      static sptr make(const std::vector<std::vector<gr_complex> >& preamble_seq, const std::vector<int>& n_repeats, float thres);

      // debug internal variables
      virtual std::vector<gr_complex> get_crosscorr0(int N) = 0;
      virtual std::string get_crosscorr0_peaks() = 0;
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FRAME_SYNC_CC_H */

