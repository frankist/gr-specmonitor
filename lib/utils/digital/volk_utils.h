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
#include <gnuradio/filter/fir_filter_with_buffer.h>
#include <vector>

#ifndef VOLK_UTILS_H_
#define VOLK_UTILS_H_

namespace volk_utils {

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

    volk_array(const volk_array<T>& v) : d_capacity(0) {
      resize(v.capacity());
      std::copy(&v[0], &v[v.capacity()], &vec[0]);
    }

    ~volk_array() {
      if(capacity()>0)
        volk_free(vec);
    }

    inline size_t capacity() const { return d_capacity; }

    volk_array<T> operator=(const volk_array<T>& v) {
      return volk_array(v);
    }

    inline void resize(size_t cap) {
      if(d_capacity>0)
        volk_free(vec);
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
  struct hist_volk_array {
    volk_array<T> vec;
    int d_hist_len;

    hist_volk_array() : d_hist_len(0) {
    }

    hist_volk_array(int h_len, int len) : vec(len+h_len), d_hist_len(h_len) {
    }

    void resize(int h_len, int len) {
      vec.resize(len+h_len);
      d_hist_len = h_len;
    }

    inline T& operator[](int i) {
      assert(i>=-hist_len() && i <= size());
      return vec[i+hist_len()];
    }

    inline const T& operator[](int i) const {
      assert(i>=-hist_len() && i <= size());
      return vec[i+hist_len()];
    }

    inline void advance(int siz) {
      std::copy(&vec[siz], &vec[siz+hist_len()], &vec[0]);
    }

    inline int size() const {
      return ((int)vec.capacity()) - d_hist_len;
    }

    inline int hist_len() const {
      return d_hist_len;
    }
  };

  template<typename T>
  class volk_matrix {
  public:
    volk_array<T> vec;
    int d_nrows;
    int d_ncols;

    volk_matrix(unsigned int nrows, unsigned int ncols) :
      vec(nrows*ncols), d_nrows(nrows), d_ncols(ncols) {
    }

    T& at(int row, int col) {
      assert(row>=0 && col>=0 && row < d_nrows && col < d_ncols);
      return vec[col*d_nrows + row];
    }

    inline int ncols() const {return d_ncols;}
    inline int nrows() const {return d_nrows;}
    inline int length() const {return d_nrows*d_ncols;}
  };

  class moving_average_ff {
  public:
    volk_array<float> d_xbuf;
    volk_array<float> d_xtmp;
    unsigned int d_size;
    int d_i;

    moving_average_ff(size_t len) :
      d_xbuf(len), d_xtmp(len), d_size(len), d_i(0) {
      std::fill(&d_xbuf[0],&d_xbuf[d_size],0);
      std::fill(&d_xtmp[0],&d_xtmp[d_size],0);
    }

    void execute(float *x, float *res, size_t x_len) {
      for(int i = 0; i < x_len; ++i) {
        d_xbuf[d_i] = x[i];
        volk_32f_accumulator_s32f(&d_xtmp[0], &d_xbuf[0], d_size);
        res[i] = d_xtmp[0];
        d_i = (d_i + 1) % d_size;
      }
      volk_32f_s32f_normalize(res, (float)d_size, x_len);
    }

    float execute(float x) {
      d_xbuf[d_i] = x;
      volk_32f_accumulator_s32f(&d_xtmp[0], &d_xbuf[0], d_size);
      d_i = (d_i + 1) % d_size;
      return d_xtmp[0]/(float) d_size;
    }

    inline float mean() const {
      return d_xtmp[0]/(float) d_size;
    }

    inline size_t size() const {
      return d_size;
    }
  };

  class hist_moving_average_ff {
  public:
    volk_array<float> d_xcsum;
    int mavg_size;

    hist_moving_average_ff(size_t capacity, size_t len) :
      d_xcsum(capacity), mavg_size(len) {}

    void execute(const hist_volk_array<float>& x, float* res, size_t xlen) {
      // basically the "implicit" refresh happens in every call
      volk_32f_accumulator_s32f(&d_xcsum[0], &x[-mavg_size], xlen+mavg_size);
      volk_32f_x2_subtract_32f(res, &d_xcsum[mavg_size], &d_xcsum[0], xlen);
    }

    inline size_t size() const {
      return mavg_size;
    }
  };


  // class moving_average_ff {
  // public:
  //   gr::filter::kernel::fir_filter_with_buffer_fff* d_filter;

  //   moving_average_ff(size_t len) {
  //     d_filter = new gr::filter::kernel::fir_filter_with_buffer_fff(std::vector<float>(len,1));
  //     assert(len>0);
  //   }

  //   // Note: I have to define the copy constructor bc I have an internal pointer
  //   moving_average_ff(const moving_average_ff& m) {
  //     d_filter = new gr::filter::kernel::fir_filter_with_buffer_fff(m.d_filter->taps());
  //   }

  //   ~moving_average_ff() {
  //     delete d_filter;
  //   }

  //   moving_average_ff operator=(const moving_average_ff& m) {
  //     return moving_average_ff(m);
  //   }

  //   void execute(float *x, float *res, size_t x_len) {
  //     d_filter->filterN(res, x, x_len);
  //     volk_32f_s32f_normalize(res, (float)d_filter->ntaps(), x_len);
  //   }

  //   float execute(const float& x) {
  //     return d_filter->filter(x)/d_filter->ntaps();
  //   }

  //   inline size_t size() const {
  //     return d_filter->ntaps();
  //   }
  // };

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
      volk_free(d_tmp);
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

  private:
    moving_average(const moving_average& m) {} // Note: I have to disable the copy constructor due to internal ptrs
    moving_average<T>& operator=(const moving_average& m) {} // Note: disable this one too
  };

  void compensate_cfo(gr_complex *y, const gr_complex* x, float frac_cfo, int len,
                         gr_complex phase_init = gr_complex(1.0f,0.0f)) {
    lv_32fc_t phase_increment = lv_cmake(std::cos(-frac_cfo*(float)(2*M_PI)),std::sin(-frac_cfo*(float)(2*M_PI)));
    // lv_32fc_t phase_init = lv_cmake(1.0f,0.0f);

    volk_32fc_s32fc_x2_rotator_32fc(y, x, phase_increment, &phase_init, len);
    // for(int n = 0; n < len1 + 2*d_corr_margin; ++n)
    //   d_in_cfo[n] = in[start_idx+n]*std::exp(std::complex<float>(0,-2*M_PI*d_peaks[i].cfo*n));
  }
};

#endif
