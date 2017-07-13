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
#include <cmath>

#ifndef ZADOFFCHU_H_
#define ZADOFFCHU_H_

namespace utils {
  template<typename complex_type>
  void generate_zc_sequence(complex_type* x, int u, int q, int zc_len) {
    int N = zc_len;

    for(int n = 0; n < N; ++n)
      x[n] = std::exp(complex_type(0,-M_PI*u*n*(n+1+2*q)/zc_len));
  }
};

#endif
