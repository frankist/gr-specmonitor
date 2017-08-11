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

#include <complex>

#ifndef OPERATION_UTILS_H_
#define OPERATION_UTILS_H_

namespace utils {
  template<typename complex_type>
  inline float mean_mag2(complex_type* vec, int N) {
    float sum = 0;
    for(int i = 0; i < N; ++i)
      sum += std::norm(vec[i]);
    return sum;
  }

  class OpNorm {
    inline float operator()(std::complex<float> val) {
      return std::norm(val);
    }
  };
  float OpAccNorm (float x, std::complex<float> y) {return x+std::norm(y);}
};

#endif
