/* -*- c++ -*- */
/* 
 * Copyright 2018 <+YOU OR YOUR COMPANY+>.
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


#ifndef INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H
#define INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H

#include <specmonitor/api.h>
#include <complex>
#include "../../lib/utils/digital/volk_utils.h"
#include "../../lib/utils/digital/range_utils.h"
#include "../../lib/utils/digital/hist_algorithm.h"
#include "frame_params.h"

typedef std::complex<float> cplx;

namespace gr {
namespace specmonitor {
  class PyFrameParams;

  class SPECMONITOR_API PyPreambleParams {
  protected:
    HierPreambleParams params;
  public:
    // NOTE: I didn't use inheritance because swig does not get it
    PyPreambleParams(const std::vector<std::vector<cplx> >& plist,
                   const std::vector<int>& plist_seq,
                   const std::vector<cplx>& plist_coef);
    inline const std::vector<cplx>& subseq(int i) const {return params.subseq(i);}
    inline const std::vector<cplx>& subseq_norm(int i) const {return params.subseq_norm(i);}
    inline const std::vector<cplx>& argcoef_subseq() const {return params.argcoef_subseq();}
    inline const std::vector<int>& argidxs_subseq() const {return params.argidxs_subseq();}
    inline int length() const {return params.length();}
    inline const std::vector<cplx>& preamble() const {return params.preamble();}
    friend class PyFrameParams;
  };
  // HierPreambleParams generate_hier_preamble(std::vector<int> subseq_len_list,
  //                                        int n_subseq0, int num_repeats=1);

  class SPECMONITOR_API PyFrameParams {
    // Frame structure: [awgn_len | preamble | guard0 | guard1 | section | guard2 | guard3]
    HierFrameParams fparams;
  public:
    PyFrameParams(PyPreambleParams pyparams, int glen, int awgnlen, int frameperiod);
    inline PyPreambleParams preamble_params() const {
      const HierPreambleParams &p = fparams.preamble_params;
      return PyPreambleParams(p.subseq_list(),p.argidxs_subseq(),p.argcoef_subseq());
    }
    inline int section_duration() const {return fparams.section_duration();}
    inline std::pair<int,int> section_interval() const {return fparams.section_interval();}
    inline int guarded_section_duration() const {return fparams.guarded_section_duration();}
    inline std::pair<int,int> guarded_section_interval() const {return fparams.guarded_section_interval();}
    inline std::pair<int,int> preamble_interval() const {return fparams.preamble_interval();}
    inline int awgn_gap_size() const {return fparams.awgn_len;}
    inline int guard_length() const {return fparams.guard_len;}
    inline int frame_period() const {return fparams.frame_period;}
  };

  class SPECMONITOR_API PyTrackedPeak {
  public:
    int tidx;
    float xcorr;
    float xautocorr;
    float cfo;
    float preamble_mag2;
    float awgn_mag2_nodc;
    cplx dc_offset;

    PyTrackedPeak(int tpeak, float xcorr_peak,
                  float xautocorr_peak, float cfo_peak,
                  float xmag2, float awgn_estim_nodc,
                  cplx dc_offset_peak);
    inline float snr() const {
      return (preamble_mag2>=awgn_mag2_nodc) ? (preamble_mag2-awgn_mag2_nodc)/awgn_mag2_nodc : 0;
    }
    inline float SNRdB() const {return 10*log10(snr());}
    std::string print();
  };

/*!
  * \brief <+description+>
  *
  */
class SPECMONITOR_API hier_preamble_detector
{
public:
  hier_preamble_detector(PyFrameParams fparams, int autocorr_margin = -1, float thres1 = 0.08, float thres2 = 0.04);
  // hier_preamble_detector() : d_fparams(), d_pparams(d_fparams.preamble_params) {}
  ~hier_preamble_detector();
  void work(const std::vector<cplx > x_h);
  void work(const cplx* x_h, int nsamples);
  void work(const utils::hist_array_view<const cplx >&x_h);
  std::vector<float> find_crosscorr_peak(int tpeak);

  // arguments
  PyFrameParams d_fparams;
  int d_autocorr_margin;
  float d_thres1;
  float d_thres2;

  // derived
  PyPreambleParams d_pparams;
  utils::array_view<const cplx> d_lvl2_seq;
  std::vector<cplx> d_lvl2_seq_diff;
  utils::array_view<const cplx> P0;
  int L;
  int l0;
  int l1;
  int L0;
  int N_awgn;
  int N_margin;

  // internal
  long d_nread;
  int d_margin;
  std::vector<int> d_delay;
  std::vector<int> d_delay2;
  std::vector<int> d_delay_cum;
  std::vector<int> d_delay2_cum;
  int d_hist_len;
  int d_hist_len2;
  int d_Ldiff;
  int d_x_hist_len;
  std::vector<int> d_local_peaks;
  std::vector<PyTrackedPeak> d_peaks;

 private:
  // internal buffers
  volk_utils::hist_volk_array<cplx > x_h;
  volk_utils::hist_volk_vector<cplx > xdc_mavg_h;
  volk_utils::hist_volk_vector<cplx > xnodc_h;
  volk_utils::hist_volk_vector<cplx > xschmidl_nodc_h;
  std::vector<cplx > xschmidl_filt_nodc;
  volk_utils::hist_volk_vector<float> xcorr_nodc_h;
  std::vector<float> xcorr_filt_nodc;
  volk_utils::hist_volk_vector<float> xcrossautocorr_nodc_h;
  utils::SlidingWindowMaxHist* local_max_finder_h;

  std::vector<cplx> d_tmp;
  std::vector<cplx> d_tmp2;

  // this is for debug in python mostly
 public:
  inline std::vector<cplx > DC_moving_average_buffer() const {
    return xdc_mavg_h.vector_clone();
  }
  inline int DC_moving_average_buffer_hist_len() const {
    return xdc_mavg_h.hist_len();
  }
  inline std::vector<cplx > DC_cancelled_buffer() const {
    return xnodc_h.vector_clone();
  }
  inline int DC_cancelled_buffer_hist_len() const {
    return xnodc_h.hist_len();
  }
  inline std::vector<cplx > SCox_noDC_buffer() const {
    return xschmidl_nodc_h.vector_clone();
  }
  inline int SCox_noDC_hist_len() const {
    return xschmidl_nodc_h.hist_len();
  }
  inline std::vector<cplx > SCox_filt_buffer() const {
    return xschmidl_filt_nodc;
  }
  inline std::vector<float> crosscorrelation_noDC_buffer() const {
    return xcorr_nodc_h.vector_clone();
  }
  inline int crosscorrelation_noDC_hist_len() const {
    return xcorr_nodc_h.hist_len();
  }
  inline std::vector<float> crosscorrelation_filt_buffer() const {
    return xcorr_filt_nodc;
  }
  inline std::vector<float> test_statistics_buffer() const {
    return xcrossautocorr_nodc_h.vector_clone();
  }
  inline int test_statistics_hist_len() const {
    return xcrossautocorr_nodc_h.hist_len();
  }
  inline std::vector<PyTrackedPeak> peaks() const {return d_peaks;}
};

  // This is to call it from python
  // hier_preamble_detector make_hier_preamble_detector_from_json(std::string js) {
  //   return hier_preamble_detector(FrameParams());
  // }

} // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_HIER_PREAMBLE_DETECTOR_H */

