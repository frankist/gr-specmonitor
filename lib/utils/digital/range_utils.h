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

#include <cassert>
#include <algorithm>
#include <limits>
#include <vector>
#include <iostream>

#ifndef RANGE_UTILS_H_
#define RANGE_UTILS_H_

namespace utils {
  template<typename T>
  struct array_view {
    T* d_begin;
    T* d_end;
    typedef T* iterator;
    typedef const T* const_iterator;

    array_view() : d_begin(NULL), d_end(NULL) {}
    array_view(const T* b, const T* e) : d_begin(b), d_end(e) {}
    template<typename It>
    array_view(const It b, const It e) : d_begin(&(*b)), d_end(&(*e)) {}
    void reset(T* b, T* e) {d_begin = b; d_end = e;}
    inline array_view<T>::iterator begin() {return d_begin;}
    inline array_view<T>::iterator end() {return d_end;}
    inline array_view<T>::const_iterator begin() const {return d_begin;}
    inline array_view<T>::const_iterator end() const {return d_end;}
    inline T* endref() {return d_end;}
    inline const T* endref() const {return d_end;}
    inline T& operator[](size_t i) {
      assert(i<=size());
      return *(d_begin+i);}
    inline const T& operator[](size_t i) const {
      assert(i<=size());
      return *(d_begin+i);
    }
    inline size_t size() const {return d_end-d_begin;}
    inline std::vector<T> vector_clone() const {
      return std::vector<T>(d_begin,d_end);
    }
  };

  template<typename T>
  struct hist_array_view {
    array_view<T> vec;
    int d_hist_len;

    hist_array_view() : d_hist_len(0) {}

    // hist_array_view(T* vec_x, int h_len) :
    //   vec(vec_x,vec_x+),
    //   hist_len(h_len),
    //   d_size(std::numeric_limits<int>::max()) {
    // }

    hist_array_view(T* vec_x, int h_len, int siz) :
      vec(vec_x,vec_x+siz+h_len),
      d_hist_len(h_len) {
    }

    int size() const {return vec.size()-d_hist_len;}

    void reset(T* vec_x, int h_len, int siz = std::numeric_limits<int>::max()) {
      vec.reset(vec_x,vec_x+h_len+siz);
      d_hist_len = h_len;
    }

    inline T& operator[](int i) {
      assert(i>=-d_hist_len && i <= size());
      return vec[i+hist_len()];
    }

    inline const T& operator[](int i) const {
      assert(i>=-d_hist_len && i <= size());
      return vec[i+hist_len()];
    }

    inline int hist_len() const {
      return d_hist_len;
    }
    inline void advance(int siz) {
      std::copy(&vec[siz], &vec[siz+d_hist_len], &vec[0]);
    }
    inline std::vector<T> vector_clone() const {
      return vec.vector_clone();
    }
  };

  template<typename T>
  class matrix {
  public:
    std::vector<T> vec;
    int d_nrows;
    int d_ncols;
    typedef typename std::vector<T>::iterator iterator;

    matrix(unsigned int nrows, unsigned int ncols) :
      vec(nrows*ncols), d_nrows(nrows), d_ncols(ncols) {
    }

    T& at(int row, int col) {
      assert(row>=0 && col>=0 && row <= d_nrows && col <= d_ncols);
      return vec[col*d_nrows + row];
    }

    matrix<T>::iterator begin() {return vec.begin();}
    matrix<T>::iterator end() {return vec.end();}

    inline int ncols() const {return d_ncols;}
    inline int nrows() const {return d_nrows;}
    inline int length() const {return d_nrows*d_ncols;}
  };
}

#endif
