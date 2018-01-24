#ifndef HIST_ALGORITHM_H_
#define HIST_ALGORITHM_H_

#include <algorithm>
#include <numeric>
#include <cassert>

typedef std::complex<float> cplx;

namespace utils {

  // version without history
  template<typename T>
  inline void moving_average_nohist(T* y, const T* x, const T* xend, size_t mavgsize) {
    int l = (xend-x)-mavgsize+1;
    assert(l>0 && &x[l+mavgsize-1]==xend);
    for(int i = 0; i < l; ++i) {
      y[i] = std::accumulate(&x[i],&x[i+mavgsize],(T)0)/(T)mavgsize;
    }
  }

  template<typename T>
  inline void moving_average_hist(T* y, const T* x,
                                  const T* xend, size_t mavgsize) {
    moving_average_nohist(y, x-mavgsize+1, xend, mavgsize);
  }

  template<typename T>
  inline void correlate(T* y, const T* x, const T* xend, const T* taps, int ntaps) {
    int N = (xend-x)-ntaps+1;
    for(int i = 0; i < N; ++i) {
      volk_32fc_x2_conjugate_dot_prod_32fc(&y[i], &x[i], &taps[0], ntaps);
    }
  }

  template<typename T>
  inline void correlate_hist(T* y, const T* x, const T* xend, const T* taps, int ntaps) {
    correlate(y, x-ntaps+1, xend, taps, ntaps);
  }

  template<typename Vec, typename HistVec, typename Vec2>
  inline void correlate_hist(Vec& y, const HistVec& x, const Vec2& taps) {
    assert(y.size()>=x.size());
    correlate(&y[0], &x[-taps.size()+1], &x[x.size()], &taps[0], taps.size());
  }

  template<typename T>
  inline void interleaved_sum(T* y, const T* x1, const T* x1_end,
                              int num_sums, int interleav_len) {
    int winsize = interleav_len*num_sums;
    int N = (x1_end-x1)-winsize+1;
    for(int i = 0; i < N; ++i) {
      y[i] = 0;
      int k = 0;
      for(int j = i; j < i+winsize; j+=interleav_len) {
        y[i] += x1[j];
      }
    }
  }

  template<typename T>
  inline void interleaved_sum_hist(T* y, const T* x1, const T* x1_end,
                                   int num_sums, int interleav_len) {
    int winsize = interleav_len*num_sums;
    interleaved_sum(y, x1-winsize+1, x1_end, num_sums, interleav_len);
  }

  template<typename Vec, typename HistVec>
  inline void interleaved_sum_hist(Vec& y, const HistVec& x1,
                                   int num_sums, int interleav_len) {
    int winsize = interleav_len*num_sums;
    assert(y.size()>=x1.size()-winsize+1);
    interleaved_sum(&y[0], &x1[-winsize+1], &x1[x1.size()], num_sums, interleav_len);
  }

  template<typename T>
  inline void interleaved_crosscorrelate(T* y, const T* x1, const T* x1_end,
                                         const T* x2, const T* x2_end, int interleav_len) {
    int winsize = interleav_len*(x2_end-x2);
    int N = (x1_end-x1)-winsize+1;
    for(int i = 0; i < N; ++i) {
      y[i] = 0;
      int k = 0;
      for(int j = i; j < i+winsize; j+=interleav_len) {
        y[i] += x1[j]*x2[k++];
      }
    }
  }

  template<typename T>
  inline void interleaved_crosscorrelate_hist(T* y, const T* x1, const T* x1_end,
                                              const T* x2, const T* x2_end, int interleav_len) {
    int winsize = interleav_len*(x2_end-x2);
    interleaved_crosscorrelate(y, x1-winsize+1, x1_end, x2, x2_end, interleav_len);
  }

  template<typename Vec, typename HistVec>
  inline void interleaved_crosscorrelate_hist(Vec& y, const HistVec& x1,
                                              const Vec& x2, int interleav_len) {
    int winsize = interleav_len*x2.size();
    assert(y.size()>=x1.size()-winsize+1);
    interleaved_crosscorrelate(&y[0], &x1[-winsize+1], &x1[x1.size()],
                               &x2[0], &x2[x2.size()], interleav_len);
  }

  template<typename T>
  inline void compute_schmidl_cox(T* y, const T* x, const T* xend, int nBins_half) {
    // NOTE: Implement in the future a moving autocorrelation for efficiency
    int dim = (xend-x)-2*nBins_half+1;
    for(int i = 0; i < dim; ++i) {
      cplx result;
      volk_32fc_x2_conjugate_dot_prod_32fc(&result, &x[i], &x[i+nBins_half], nBins_half);
      y[i] = result;
    }
  }

  template<typename T>
  inline void compute_schmidl_cox_hist(T* y, const T* x, const T* xend, int nBins_half) {
    compute_schmidl_cox(y, x-nBins_half*2+1, xend, nBins_half);
  }

  template<typename Vec, typename HistVec>
  inline void compute_schmidl_cox_hist(Vec& y, const HistVec& x, int nBins_half) {
    // This version has more safety through asserts implicit to HistVec
    assert(y.size()>=x.size());
    compute_schmidl_cox(&y[0], &x[-nBins_half*2+1], &x[x.size()], nBins_half);
  }

  float compute_schmidl_cox_cfo(const cplx& c, int nBins_half) {
    return -std::arg(c)/(2*M_PI*nBins_half);
  }

  struct SlidingWindowMaxHist {
    int d_xidx;
    int d_margin;

    SlidingWindowMaxHist(int margin) :
      d_margin(margin),
      d_xidx(0) {
    }

    template<typename T>
    void work(std::vector<int>& peaks, const T* x, int N = -1) {
      int i_end = N - d_margin;
      while(d_xidx < i_end) {
        const T* max_ptr = std::max_element(&x[d_xidx+1],&x[d_xidx+d_margin]);
        if(*max_ptr >= x[d_xidx]) {
          d_xidx = std::distance(x, max_ptr);
          continue;
        }
        peaks.push_back(d_xidx);
        d_xidx += d_margin;
      }
      d_xidx -= N; //starts from a negative point, most of the time at "-margin"
    }
  };
}
#endif
