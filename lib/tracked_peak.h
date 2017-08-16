/* -*- c++ -*- */
/* 
 * Copyright 2017 <+YOU OR YOUR COMPANY+>.
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

#include <gnuradio/gr_complex.h>

#ifndef _TRACKED_PEAK_CC_H_
#define _TRACKED_PEAK_CC_H_

namespace gr {
  namespace specmonitor {
    struct crosscorr_peak {
      long idx;
      float corr_mag;
      float preamble_mag2;
      gr_complex autocorr_val;
      float awgn_mag2;

      crosscorr_peak(long peak_idx, float crosscorr_mag, float mag2, gr_complex acorr_val, float awgn_estim) :
        idx(peak_idx),
        corr_mag(crosscorr_mag),
        preamble_mag2(mag2),
        autocorr_val(acorr_val),
        awgn_mag2(awgn_estim) {}
      inline float SNRdB() const {return 10*log10(snr());}
      inline float snr() const {return (preamble_mag2-awgn_mag2)/awgn_mag2;}
    };

    class tracked_peak {
    public:
      double peak_idx;        //< time stamp where the preamble starts
      float peak_corr;        //< abs(crosscorr(signal,preamble))
      float peak_mag2;        //< mean(abs(signal)**2)
      float cfo;              //< CFO (**not** in radians)
      float awgn_estim;       //< AWGN estimation

      int n_frames_elapsed;
      int n_frames_detected;
      int n_missed_frames_contiguous;
      bool p_first_flag;

      // tracked_peak() : n_frames_elapsed(0), n_frames_detected(0), p_first_flag(true), n_missed_frames_contiguous(0) {}
      tracked_peak(long idx, float pcorr, float pmag2, float cfo_x, float awgn_est);
      void update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period);
      void update_cfo(gr_complex res, int len0);
      void update_awgn(float new_awgn);
      void update_mag2(float new_mag2);
      inline float SNRdB() const {return 10*log10(peak_mag2/awgn_estim);}
      inline float snr() const {return peak_mag2/awgn_estim;}
    };

    tracked_peak::tracked_peak(long idx, float pcorr, float pmag2, float cfo_x, float awgn_est) :
      peak_idx((double)idx),
      peak_corr(pcorr),
      peak_mag2(pmag2),
      cfo(cfo_x),
      awgn_estim(awgn_est),
      n_frames_elapsed(0),
      n_frames_detected(0),
      n_missed_frames_contiguous(0),
      p_first_flag(true) {
    }

    void tracked_peak::update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period) {
      if(corramp > thres) {
        if(p_first_flag==true) {
          peak_corr = corramp;
          peak_mag2 = mag2;
          peak_idx = new_peak;
          p_first_flag = false;
        }
        else {
          peak_idx = 0.95*peak_idx + 0.05*new_peak;
          peak_corr = 0.95*peak_corr + 0.05*corramp;
          peak_mag2 = 0.95*peak_mag2 + 0.05*mag2;
        }
        n_frames_detected++;
        n_missed_frames_contiguous=0;
      }
      else {
        std::cout << "WARNING: The peak was missed. The crosscorr params were: {"
                  << new_peak << "," << corramp << "}"  << std::endl;
        n_missed_frames_contiguous++;
      }
    }

    void tracked_peak::update_cfo(gr_complex res, int len0) {
      float cfo_new = -std::arg(res)/(2*M_PI*len0);
      cfo = 0.95*cfo + 0.05*cfo_new;
    }

    void tracked_peak::update_awgn(float new_awgn) {
      awgn_estim = 0.95*awgn_estim + 0.05*new_awgn;
    }

    void tracked_peak::update_mag2(float new_mag2) {
      peak_mag2 = 0.95*peak_mag2 + 0.05*new_mag2;
    }

    std::string println(const tracked_peak& t) {
      std::stringstream ss;
      ss << "{" << t.peak_idx << "," << t.peak_corr
         << "," << t.peak_mag2 << "," << t.cfo << "," << t.awgn_estim << "}";
      return ss.str();
    }

  }
}

#endif
