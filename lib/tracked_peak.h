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
    float compute_cfo(gr_complex val, int len0) {
      return -std::arg(val)/(2*M_PI*len0);
    }

    struct crosscorr_peak {
      long tidx;                   //< time stamp where the preamble starts
      float corr_mag;              //< abs(crosscorr(signal,preamble))
      float preamble_mag2;         //< mean(abs(signal)**2)
      gr_complex autocorr_val;     //< result of an autocorrelation (schmidl&cox)
      float awgn_mag2;             //< AWGN estimation
      int len0;

      crosscorr_peak(long peak_idx, float crosscorr_mag, float mag2, gr_complex acorr_val, float awgn_estim, int len0_x) :
        tidx(peak_idx),
        corr_mag(crosscorr_mag),
        preamble_mag2(mag2),
        autocorr_val(acorr_val),
        awgn_mag2(awgn_estim),
        len0(len0_x) {}
      inline float SNRdB() const {return 10*log10(snr());}
      inline float snr() const {return (preamble_mag2-awgn_mag2)/awgn_mag2;}
      inline float cfo() const {return compute_cfo(autocorr_val,len0);}
    };

    class tracked_peak : public crosscorr_peak {
      double d_peak_idx;        //< time stamp where the preamble starts
    public:
      int peakno;

      int n_frames_elapsed;
      int n_frames_detected;
      int n_missed_frames_contiguous;
      bool p_first_flag;

      // tracked_peak() : n_frames_elapsed(0), n_frames_detected(0), p_first_flag(true), n_missed_frames_contiguous(0) {}
      tracked_peak(long idx, float pcorr, float pmag2, gr_complex aval, float awgn_est, int len0, int id_x);
      void update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period);
      void update_cfo(gr_complex res, int len0);
      void update_awgn(float new_awgn);
      void update_mag2(float new_mag2);
      inline float SNRdB() const {return 10*log10(preamble_mag2/awgn_mag2);}
      inline float snr() const {return preamble_mag2/awgn_mag2;}

      inline long peak_idx() const { return tidx; }
      inline long increment_peak_idx(long val) { d_peak_idx += val; tidx += val; }
    };

    tracked_peak::tracked_peak(long idx, float pcorr, float pmag2, gr_complex aval, float awgn_est, int len0, int id_x) :
      crosscorr_peak(idx, pcorr, pmag2,
                     aval, awgn_est, len0), //FIXME: I have to have len0 here
      d_peak_idx((double)idx),
      peakno(id_x),
      n_frames_elapsed(0),
      n_frames_detected(0),
      n_missed_frames_contiguous(0),
      p_first_flag(true) {
    }

    void tracked_peak::update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period) {
      if(corramp > thres) {
        if(p_first_flag==true) {
          corr_mag = corramp;
          preamble_mag2 = mag2;
          d_peak_idx = new_peak;
          p_first_flag = false;
          tidx = (long)round(d_peak_idx);
        }
        else {
          d_peak_idx = 0.95*d_peak_idx + 0.05*new_peak;
          tidx = (long)round(d_peak_idx);
          corr_mag = 0.95*corr_mag + 0.05*corramp;
          preamble_mag2 = 0.95*preamble_mag2 + 0.05*mag2;
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
      autocorr_val = 0.95f*autocorr_val + 0.05f*res;
    }

    void tracked_peak::update_awgn(float new_awgn) {
      awgn_mag2 = 0.95*awgn_mag2 + 0.05*new_awgn;
    }

    void tracked_peak::update_mag2(float new_mag2) {
      preamble_mag2 = 0.95*preamble_mag2 + 0.05*new_mag2;
    }

    std::string println(const tracked_peak& t) {
      std::stringstream ss;
      ss << "{" << t.tidx << "," << t.corr_mag
         << "," << t.preamble_mag2 << "," << t.cfo() << "," << t.awgn_mag2 << "}";
      return ss.str();
    }

  }
}

#endif
