#ifndef HIST_ALGORITHM_H_
#define HIST_ALGORITHM_H_

#include <algorithm>
#include <numeric>
#include <cassert>

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

}
#endif
