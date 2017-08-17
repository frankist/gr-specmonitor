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

#include <volk/volk.h>
#include <vector>

#ifndef VOLK_UTILS_H_
#define VOLK_UTILS_H_

namespace volk_utils {
  template<typename T>
  class moving_average {
  public:
    T* d_vec;
    T* d_tmp;
    size_t d_capacity;
    size_t d_size;
    int d_i;
    T d_sum;

    moving_average(size_t len) : d_size(len), d_i(0) {
      d_capacity = (size_t)(floor(len/1024)+1)*1024;
      d_vec = (T*) volk_malloc(sizeof(T) * d_capacity, volk_get_alignment());
      d_tmp = (T*) volk_malloc(sizeof(T) * d_capacity, volk_get_alignment());
      std::fill(&d_vec[0], &d_vec[d_size], T(0));
      d_sum = T(0);
    }

    ~moving_average() {
      volk_free(d_vec);
    }

    void execute(T* x, size_t x_len) {
      int i2 = d_i;
      for(int i = 0; i < x_len; ++i) {
        i2 = (d_i+i)%d_size;
        d_vec[i2] = x[i];
      }
      refresh();
      d_i = i2;
    }

    void execute(T* x, T* res, size_t x_len) {
      int i2 = d_i;
      for(int i = 0; i < x_len; ++i) {
        i2 = (d_i+i)%d_size;
        // d_sum += x[i] - d_vec[i2];
        d_vec[i2] = x[i];
        refresh();
        res[i] = mean();
      }
      // if(d_i+x_len >= d_size)
      //   refresh();
      d_i = i2;
    }

    T execute(T x) {
      d_sum += x - d_vec[d_i];
      d_vec[d_i] = x;
      d_i++;
      if(d_i>=d_size) {
        d_i -= d_size;
        refresh();
      }
      return mean();
    }

    inline T mean() const {
      return d_sum/(T)d_size;
    }

    void refresh() {
      volk_32f_accumulator_s32f(&d_tmp[0], &d_vec[0], d_size);
      d_sum = d_tmp[0];
    }

    inline size_t size() const {
      return d_size;
    }
  };

  template<typename T>
  struct volk_array {
    T* vec;
    size_t d_capacity;

    volk_array() : d_capacity(0) {
    }

    volk_array(size_t cap) : d_capacity(cap) {
      assert(cap>0);
      vec = (T*) volk_malloc(sizeof(T)*cap, volk_get_alignment());
    }

    volk_array(const volk_array<T>& v) {
      resize(v.capacity());
      std::copy(&v[0], &v[v.capacity()], &vec[0]);
    }

    ~volk_array() {
      if(capacity()>0)
        volk_free(vec);
    }

    inline size_t capacity() const { return d_capacity; }

    volk_array<T>& operator=(const volk_array<T>& v) {
      return volk_array(v);
    }

    inline void resize(size_t cap) {
      d_capacity = cap;
      vec = (T*) volk_malloc(sizeof(T)*cap, volk_get_alignment());
    }

    inline T& operator[](int i) {
      assert(i>=0 && i <= capacity());
      return vec[i];
    }

    inline const T& operator[](int i) const {
      assert(i>=0 && i <= capacity()); // I have to do <= capacity for when I want to ref the end()
      return vec[i];
    }
  };

  template<typename T>
  struct hist_array {
    T* vec;
    size_t capacity;
    size_t hist_len;

    hist_array(size_t cap, size_t h_len) :
      capacity(cap), hist_len(h_len) {
      assert(hist_len < capacity);
      vec = (T*) volk_malloc(sizeof(T)*cap, volk_get_alignment());
    }

    ~hist_array() {
      volk_free(vec);
    }

    inline T& operator[](int i) {
      assert(i>=-hist_len && i < capacity-hist_len);
      return vec[i-hist_len];
    }

    inline void advance(int siz) {
      assert(siz+hist_len <= capacity);
      std::copy(&vec[siz], &vec[siz+hist_len], &vec[0]);
    }
  };
};

#endif
