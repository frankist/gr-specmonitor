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
  float OpNorm(cplx val) {return std::norm(val);}
  float OpAccNorm (float x, std::complex<float> y) {return x+std::norm(y);}
  float OpNormComp(cplx x, cplx y) { return std::norm(x) < std::norm(y); }
  struct OpAccNormDist {
    cplx val;
    OpAccNormDist(cplx a) : val(a) {}
    inline float operator()(float x, cplx y) const {return x+std::norm(y-val);}
  };

  inline cplx mean(const cplx* x, int N) {
    return std::accumulate(x,x+N,cplx(0,0))/(float)N;
  }
  inline float mean_mag2(const cplx* x, int N) {
    return std::accumulate(x,x+N,0.0f,OpAccNorm)/(float)N;
  }
  inline float mean_mag2_bias(const cplx* x, int N, cplx bias) {
    OpAccNormDist op(bias);
    return std::accumulate(x,x+N,0.0f,op)/(float)N;
  }

  // template<typename complex_type>
  // inline float mean_mag2(const complex_type* vec, int N) {
  //   float sum = 0;
  //   for(int i = 0; i < N; ++i)
  //     sum += std::norm(vec[i]);
  //   return sum;
  // }

  // template<typename complex_type>
  // inline float mean_mag2_bias(const complex_type* vec, int N, complex_type bias) {
  //   float sum = 0;
  //   for(int i = 0; i < N; ++i)
  //     sum += std::norm(vec[i]-bias);
  //   return sum;
  // }


  template<typename T>
  inline void cumsum(T* y, const T* x, int N) {
    assert(N>0);
    y[0] = x[0];
    for(int i = 1; i < N; ++i)
      y[i] = y[i-1]+x[i];
  }
  template<typename T>
  inline std::vector<T> cumsum(const std::vector<T>& x) {
    std::vector<T> y(x.size());
    cumsum(&y[0],&x[0],x.size());
    return y;
  }

  inline int argmax(const cplx* x, int N) {
    return std::distance(x,std::max_element(x,x+N,OpNormComp));
  }
};

#endif
