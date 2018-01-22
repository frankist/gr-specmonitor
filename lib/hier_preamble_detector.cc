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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <iostream>
#include <gnuradio/io_signature.h>
#include <specmonitor/hier_preamble_detector.h>
#include "utils/digital/hist_algorithm.h"
#include "utils/prints/print_ranges.h"
#include "utils/math/transform.h"

namespace gr {
namespace specmonitor {

  PyPreambleParams::PyPreambleParams(const std::vector<std::vector<cplx> >& plist,
                                     const std::vector<int>& plist_seq,
                                     const std::vector<cplx>& plist_coef) :
    params(plist,plist_seq,plist_coef) {}

  PyFrameParams::PyFrameParams(PyPreambleParams pyparams,
                               int glen, int awgnlen, int frameperiod) :
    fparams(pyparams.params,glen,awgnlen,frameperiod) {}

  // HierPreambleParams generate_hier_preamble(std::vector<int> subseq_len_list,
  //                                        int n_subseq0, int num_repeats) {
  //   assert(subseq_len_list.size()==2);
  //   std::vector<std::vector<cplx> > pseq_list(2);
  //   // pseq_list[0] = zadoff(subseq_len_list[0],1,0);
  //   // pseq_list[1] = zadoff(subseq_len_list[1],1,0);
  //   std::vector<cplx> lvl2_code;// = maximum_length_sequence<cplx>(n_subseq0);
  //   std::vector<cplx> lvl2_many(lvl2_code.size()*num_repeats);
  //   int n=0;
  //   for(int i = 0; i < num_repeats; ++i)
  //     for(int j = 0; j < lvl2_code.size(); ++j)
  //       lvl2_many[n++] = lvl2_code[j];
  //   std::vector<cplx> pseq_list_coef;// = set_schmidl_sequence(lvl2_many);
  //   pseq_list_coef.push_back(cplx(1,0));
  //   std::vector<int> pseq_len_seq(pseq_list_coef.size()+1,0);
  //   pseq_len_seq[pseq_len_seq.size()-1] = 1;

  //   return HierPreambleParams(pseq_list,pseq_len_seq,pseq_list_coef);
  // }


  PyTrackedPeak::PyTrackedPeak(int tpeak, float xcorr_peak,
                               float xautocorr_peak, float cfo_peak,
                               float xmag2, float awgn_estim_nodc,
                               cplx dc_offset_peak) :
    tidx(tpeak), xcorr(xcorr_peak), xautocorr(xautocorr_peak),
    cfo(cfo_peak), preamble_mag2(xmag2), awgn_mag2_nodc(awgn_estim_nodc), dc_offset(dc_offset_peak) {
  }

  std::string PyTrackedPeak::print() {
    std::stringstream ss;
    ss << "[" << tidx << ", " << xcorr << ", " << xautocorr
       << ", " << cfo << ", " << preamble_mag2 << ", "
       << awgn_mag2_nodc << ", " << dc_offset << "]";
    return ss.str();
  }

  hier_preamble_detector::hier_preamble_detector(PyFrameParams fparams,
                                                 int autocorr_margin, float thres1, float thres2) :
    d_fparams(fparams),
    d_autocorr_margin(autocorr_margin),
    d_thres1(thres1),
    d_thres2(thres2),
    d_pparams(d_fparams.preamble_params()),
    d_nread(0)
{
  const std::vector<cplx > &v = d_pparams.argcoef_subseq();
  d_lvl2_seq.reset(&v[0], &v[v.size()-1]);
  const std::vector<cplx > &v2 = d_pparams.subseq_norm(0);
  P0.reset(&v2[0],&v2[v2.size()]);
  L = d_pparams.length();
  l0 = P0.size();
  l1 = d_pparams.subseq_norm(1).size();
  L0 = l0*d_lvl2_seq.size();
  d_lvl2_seq_diff = get_schmidl_sequence(d_lvl2_seq);
  N_awgn = fparams.awgn_gap_size();
  N_margin = (autocorr_margin<0) ? L0 : autocorr_margin;

  d_nread = 0;
  d_margin = 4;
  d_hist_len = N_awgn + L;
  d_delay.push_back(L0-1);
  d_delay.push_back(l0*2-1);
  d_delay.push_back(d_lvl2_seq_diff.size()*l0-1);
  d_delay2.push_back(d_delay[0]);
  d_delay2.push_back(l0-1);
  d_delay2.push_back(L0-1);
  d_delay_cum = utils::cumsum(d_delay);
  d_delay2_cum = utils::cumsum(d_delay2);
  d_hist_len2 = d_delay2_cum[2]+L+N_awgn+2*N_margin;
  d_Ldiff = std::max(l1-N_margin,0);

  // NOTE: we look back in time by self.delay_cum[2] to find peaks
  d_x_hist_len = std::max(d_delay_cum[2],L0);
  int prealloc_size = 5000;
//   // // x_h.resize(std::max(d_delay_cum[0],L0));
  xdc_mavg_h.reserve(d_delay_cum[2]-L0, prealloc_size);
  xdc_mavg_h.fill_history(cplx(0,0));
  xnodc_h.reserve(L0+d_delay_cum[0]+d_margin+l1, prealloc_size);
  xnodc_h.fill_history(cplx(0,0));
  xschmidl_nodc_h.reserve(L0, prealloc_size);
  xschmidl_nodc_h.fill_history(cplx(0,0));
  xcorr_nodc_h.reserve(L0, prealloc_size);
  xcorr_nodc_h.fill_history(0);
  xcrossautocorr_nodc_h.reserve(N_margin+d_Ldiff, prealloc_size);
  xcrossautocorr_nodc_h.fill_history(0);
  local_max_finder_h = new utils::SlidingWindowMaxHist(N_margin);
}

hier_preamble_detector::~hier_preamble_detector()
{
  delete local_max_finder_h;
}


  void hier_preamble_detector::work(const std::vector<std::complex<float> > x_h) {
    assert(x_h.size()>d_x_hist_len);
    utils::hist_array_view<const std::complex<float> > x2_h(&x_h[0],d_x_hist_len,x_h.size()-d_x_hist_len);
    work(x2_h);
  }

  void hier_preamble_detector::work(const std::complex<float>* x_h, int nsamples) {
    assert(nsamples>d_x_hist_len);
    utils::hist_array_view<const std::complex<float> > x2_h(&x_h[0],d_x_hist_len,nsamples-d_x_hist_len);
    work(x2_h);
  }

  void hier_preamble_detector::work(const utils::hist_array_view<const std::complex<float> >& x_h) {
    // compute DC
    xdc_mavg_h.flush(x_h.size());
    utils::moving_average_hist(&xdc_mavg_h[0],&x_h[0],&x_h[x_h.size()],L0);

    // cancel DC from original signal
    xnodc_h.flush(xdc_mavg_h.size());
    for(int i = 0; i < xdc_mavg_h.size(); ++i)
      xnodc_h[i] = x_h[-L0+1+i]-xdc_mavg_h[i];

    // Compute the Schmidl&Cox correlation
    xschmidl_nodc_h.flush(xnodc_h.size());
    // utils::compute_schmidl_cox_hist(&xschmidl_nodc_h[0],&xnodc_h[0],&xnodc_h.endref(),l0);
    utils::compute_schmidl_cox_hist(xschmidl_nodc_h,xnodc_h,l0);
    utils::scale(&xschmidl_nodc_h[0], 1/(float)l0, xschmidl_nodc_h.size());
    if(d_nread<d_delay_cum[1]) // null the samples that participated from the history (same as python version). NOTE: Check again why this is needed
      std::fill(&xschmidl_nodc_h[0],&xschmidl_nodc_h[std::min((int)(d_delay_cum[1]-d_nread), (int)xschmidl_nodc_h.size())],0);

    // get the SchmidlCox Multiplied by the lvl2 sequence
    xschmidl_filt_nodc.resize(xschmidl_nodc_h.size());
    // interleaved_crosscorrelate_hist(&xschmidl_filt_nodc[0],&xschmidl_nodc_h[0],&xschmidl_nodc_h[xschmidl_nodc_h.size()],d_lvl2_seq_diff,l0);
    utils::interleaved_crosscorrelate_hist(xschmidl_filt_nodc,xschmidl_nodc_h,d_lvl2_seq_diff,l0);
    utils::scale(&xschmidl_filt_nodc[0], 1/(float)d_lvl2_seq_diff.size(), xschmidl_filt_nodc.size());

    // compute crosscorrelation of x and sequence P0
    d_tmp.resize(xnodc_h.size());
    correlate_hist(d_tmp, xnodc_h, P0);
    xcorr_nodc_h.resize(d_tmp.size());
    for(int i = 0; i < xcorr_nodc_h.size(); ++i)
      xcorr_nodc_h[i] = std::norm(d_tmp[i]/(float)l0);

    // average over time in an interleaved manner
    xcorr_filt_nodc.resize(xcorr_nodc_h.size());
    utils::interleaved_sum_hist(xcorr_filt_nodc,xcorr_nodc_h,d_lvl2_seq.size(),l0);
    for(int i = 0; i < xcorr_nodc_h.size(); ++i)
      xcorr_filt_nodc[i] /= d_lvl2_seq.size();

    // get the final test statistics
    xcrossautocorr_nodc_h.resize(xcorr_filt_nodc.size());
    for(int i = 0; i < xcorr_filt_nodc.size(); ++i)
      xcrossautocorr_nodc_h[i] = std::abs(xschmidl_filt_nodc[i])*xcorr_filt_nodc[i];

    // find local peaks in the test statistic
    assert((xcrossautocorr_nodc_h.size()+d_Ldiff)==x_h.size());
    d_local_peaks.clear();
    local_max_finder_h->work(d_local_peaks, &xcrossautocorr_nodc_h[-d_Ldiff], x_h.size());
    for(int i = 0; i < d_local_peaks.size(); ++i) {
      d_local_peaks[i] -= d_Ldiff;
    }

    for(int i = 0; i < d_local_peaks.size(); ++i) {
      int t = d_local_peaks[i] - d_delay_cum[2];
      cplx dc0 = xdc_mavg_h[t+L0];
      float peak0_mag2_nodc = utils::mean_mag2_bias(&x_h[t],L0,dc0);
      float xautocorr_nodc = std::sqrt(xcrossautocorr_nodc_h[d_local_peaks[i]]);
      if(xautocorr_nodc > d_thres1 * peak0_mag2_nodc) {
        std::vector<float> peak_params = find_crosscorr_peak(t);
        float xcorr = peak_params[0];
        float cfo = peak_params[1];
        float l1mag2 = peak_params[2];
        if(l1mag2>0 and xcorr < d_thres2*l1mag2)
          continue;
        int awgn_len = d_fparams.awgn_gap_size();
        cplx dc_offset = utils::mean(&x_h[t-awgn_len],awgn_len);
        float xmag2_mavg_nodc = utils::mean_mag2_bias(&x_h[t],L,dc_offset); // for the whole preamble
        float awgn_estim_nodc = utils::mean_mag2_bias(&x_h[t-awgn_len],awgn_len,dc_offset);
        xautocorr_nodc = std::abs(xschmidl_filt_nodc[d_local_peaks[i]]);
        PyTrackedPeak p(t+d_nread,xcorr,xautocorr_nodc,cfo,
                      xmag2_mavg_nodc,awgn_estim_nodc,dc_offset);
        d_peaks.push_back(p);
        std::cout << p.print() << std::endl;
      }
    }

    d_nread += x_h.size();
  }

std::vector<float> hier_preamble_detector::find_crosscorr_peak(int tpeak) {
  float cfo = utils::compute_schmidl_cox_cfo(xschmidl_filt_nodc[tpeak+d_delay_cum[2]], l0);
  int toffset = L0+d_delay_cum[0];
  const std::vector<cplx>& pseq1 = d_pparams.subseq_norm(1);
  int twin0 = tpeak-d_margin+toffset;
  int twin1 = tpeak+pseq1.size()+d_margin+toffset;

  // compensate CFO
  d_tmp.resize(twin1-twin0);
  for(int i = 0; i < d_tmp.size(); ++i) {
    d_tmp[i] = xnodc_h[twin0+i] * std::exp(cplx(0,-2*M_PI*cfo*i));
  }

  // the CFO-compensated is multiplied by the P1
  d_tmp2.resize(d_tmp.size()-pseq1.size()+1);
  utils::correlate(&d_tmp2[0],&d_tmp[0],&d_tmp[d_tmp.size()],&pseq1[0],pseq1.size());

  // get the peak
  int maxi = utils::argmax(&d_tmp2[0],d_tmp2.size());
  float ymag2 = utils::mean_mag2(&xnodc_h[twin0+maxi],l1);
  float xcorr = std::norm(d_tmp2[maxi]/(float)pseq1.size());

  return std::vector<float>({xcorr,cfo,ymag2});
}

} /* namespace specmonitor */
} /* namespace gr */

