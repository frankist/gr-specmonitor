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

#include <gnuradio/filter/fir_filter_with_buffer.h>
#include "../utils/digital/moving_average.h"

#ifndef INTERLEAVED_FILTERING_H_
#define INTERLEAVED_FILTERING_H_

namespace gr{
namespace specmonitor {
  class interleaved_filter_ccc {
  public:
    int d_idx;
    std::vector<gr::filter::kernel::fir_filter_with_buffer_ccc*> d_filters;

    interleaved_filter_ccc(size_t n_filts, const std::vector<gr_complex>& taps) :
      d_idx(0),
      d_filters(n_filts,NULL) {
      for(int i = 0; i < n_filts; ++i)
        d_filters[i] = new gr::filter::kernel::fir_filter_with_buffer_ccc(taps);
    }

    ~interleaved_filter_ccc() {
      for(int i = 0; i < d_filters.size(); ++i)
        delete d_filters[i];
    }

    void execute(gr_complex* x, gr_complex* res, int num_samps) {
      for(int i = 0; i < num_samps; ++i) {
        res[i] = d_filters[(d_idx+i)%d_filters.size()]->filter(x[i]);
      }
      d_idx = (d_idx+num_samps)%d_filters.size();
    }

  private:
    interleaved_filter_ccc(const interleaved_filter_ccc& c) {}
    interleaved_filter_ccc operator=(const interleaved_filter_ccc& c) {}
  };

  class interleaved_filter_fff {
  public:
    int d_idx;
    std::vector<gr::filter::kernel::fir_filter_with_buffer_fff*> d_filters;

    interleaved_filter_fff(size_t n_filts, const std::vector<float>& taps) :
      d_idx(0),
      d_filters(n_filts,NULL) {
      for(int i = 0; i < n_filts; ++i)
        d_filters[i] = new gr::filter::kernel::fir_filter_with_buffer_fff(taps);
    }

    ~interleaved_filter_fff() {
      for(int i = 0; i < d_filters.size(); ++i)
        delete d_filters[i];
    }

    void execute(float* x, float* res, int num_samps) {
      for(int i = 0; i < num_samps; ++i) {
        res[i] = d_filters[d_idx]->filter(x[i]);
        d_idx = (d_idx+1)%d_filters.size();
      }
    }

    void execute(float* x, int num_samps) {
      for(int i = 0; i < num_samps; ++i) {
        d_filters[d_idx]->filter(x[i]);
        d_idx = (d_idx+1)%d_filters.size();
      }
    }

  private:
    interleaved_filter_fff(const interleaved_filter_fff& c);
    interleaved_filter_fff& operator=(const interleaved_filter_fff& c);
  };

  class interleaved_moving_average_fff : public interleaved_filter_fff {
  public:
    interleaved_moving_average_fff(size_t n_filts, size_t mavg_size) :
      interleaved_filter_fff(n_filts,
                             std::vector<float>(mavg_size,1.0/(float)mavg_size)) {
    }
  };

  class interleaved_moving_average {
  public:
    int d_idx;
    int d_len;
    std::vector<utils::moving_average<double> > d_mavg_vec;

    interleaved_moving_average(int len,int mavg_size,float val=1e-6);
    void execute(float* x, float* y, int n);
    void execute(float* x, int n);
  };

  interleaved_moving_average::interleaved_moving_average(int len,int mavg_size,float val) :
    d_idx(0), d_len(len), d_mavg_vec(len,mavg_size) {
    std::vector<double> init_vals(mavg_size,val), tmp(mavg_size);
    for (int jj = 0; jj < len; ++jj) {
      d_mavg_vec[jj].execute(&init_vals[0],&tmp[0],mavg_size);
    }
  }

  void interleaved_moving_average::execute(float* x, float*y, int n) {
    for(int i = 0; i < n; ++i) {
      y[i] = d_mavg_vec[d_idx].execute(x[i]);
      // d_mavg_vec[d_idx].execute(&x[i],&y[i],1);
      d_idx = (d_idx+1)%d_len;
    }
  }

  void interleaved_moving_average::execute(float* x, int n) {
    for(int i = 0; i < n; ++i) {
      d_mavg_vec[d_idx].execute(x[i]);
      d_idx = (d_idx+1)%d_len;
    }
  }
}
}
#endif
