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
#include <numeric>
#include "operation.h"

#ifndef TRANSFORM_UTILS_H_
#define TRANSFORM_UTILS_H_

namespace utils {
  template<typename complex_type>
  inline void conj(complex_type* vec, complex_type* result, int N) {
    for(int i = 0; i < N; ++i)
      result[i] = conj(vec[i]);
  }
  template<typename complex_type>
  inline void conj(complex_type* vec, int N) {
    for(int i = 0; i < N; ++i)
      vec[i] = conj(vec[i]);
  }

  template<typename T>
  inline void scale(T* vec, float val, size_t N) {
    for(int i = 0; i < N; ++i)
      vec[i] *= val;
  }

  template<typename T>
  inline void normalize(T* vec, size_t N) {
    float pwr = std::accumulate(&vec[0], &vec[N], 0.0, utils::OpAccNorm);
    utils::scale(&vec[0], 1/sqrt(pwr), N);
  }

  template<typename T>
  inline void set_mean_amplitude(T* vec, size_t N) {
    float amp = sqrt(std::accumulate(&vec[0], &vec[N], 0.0, utils::OpAccNorm)) / N;
    utils::scale(&vec[0], 1/amp, N);
  }
};

#endif
