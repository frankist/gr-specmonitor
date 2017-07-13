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

#ifndef MOVING_AVERAGE_H_
#define MOVING_AVERAGE_H_

namespace utils {
  template<typename T>
  class moving_average {
  public:
    std::vector<T> d_vec;
    int d_i;
    T d_sum;

    moving_average(size_t len) : d_vec(len), d_i(0) {
    }

    void execute(T* x, T* res, size_t x_len) {
      int i2 = d_i;
      for(int i = 0; i < x_len; ++i) {
        int i2 = (d_i+i)%d_vec.size();
        d_sum += x[i] - d_vec[i2];
        d_vec[i2] = x[i];
        res[i] = d_sum/d_vec.size();
      }
      if(d_i+x_len >= d_vec.size())
        refresh();

      d_i = i2;
    }

    T execute(T x) {
      d_sum += x - d_vec[d_i];
      d_vec[d_i] = x;
      d_i++;
      if(d_i>=d_vec.size()) {
        d_i -= d_vec.size();
        refresh();
      }
      return mean();
    }

    inline T mean() {
      return d_sum/(T)d_vec.size();
    }

    void refresh() {
      d_sum = 0;
      for(int i = 0; i < d_vec.size(); ++i)
        d_sum += d_vec[i];
    }
  };
};

#endif
