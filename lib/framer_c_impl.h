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

#ifndef INCLUDED_SPECMONITOR_FRAMER_C_IMPL_H
#define INCLUDED_SPECMONITOR_FRAMER_C_IMPL_H

#include <specmonitor/framer_c.h>

namespace gr
{
namespace specmonitor
{

class framer_c_impl : public framer_c
{
private:
    // Nothing to declare in this block.

public:
    framer_c_impl(double sample_rate, double frame_duration, const std::vector<gr_complex> &preamble_seq);
    ~framer_c_impl();

    // Where all the action really happens
    int work(int noutput_items,
             gr_vector_const_void_star &input_items,
             gr_vector_void_star &output_items);

private:
    double sample_rate_;         ///< Hz
    double frame_duration_;      ///< seconds
    std::vector<gr_complex> preamble_seq_;
    
    int samples_per_frame_;
    int idx_;
};

} // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_FRAMER_C_IMPL_H */

