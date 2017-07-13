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
  void conj(complex_type* vec, complex_type* result, int N) {
    for(int i = 0; i < N; ++i)
      result[i] = conj(vec[i]);
  }
  template<typename complex_type>
  void conj(complex_type* vec, int N) {
    for(int i = 0; i < N; ++i)
      vec[i] = conj(vec[i]);
  }

  template<typename T>
  void scale(T* vec, float val, int N) {
    for(int i = 0; i < N; ++i)
      vec[i] *= val;
  }
};
