/* -*- c++ -*- */
/* 
 * Copyright 2017 Francisco Paisana.
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

#include <vector>
#include <complex>

namespace utils {
  template<typename complex_type>
  float frequency_shift(complex_type* y, const complex_type* x, float frac_freq, int N, float phase_init) {
    for(int n = 0; n < N; ++n) {
      y[n] = x[n] * std::exp(complex_type(0,phase_init + 2*M_PI*frac_freq*n));
    }
    return 2*M_PI*frac_freq*N; // next phase
  }
};
