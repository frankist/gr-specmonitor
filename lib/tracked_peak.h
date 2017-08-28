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

    struct preamble_peak {
      long tidx;                   //< time stamp where the preamble starts
      float corr_mag;              //< abs(crosscorr(signal,preamble))
      float preamble_mag2;         //< mean(abs(signal)**2)
      gr_complex autocorr_val;     //< result of an autocorrelation (schmidl&cox)
      float awgn_mag2;             //< AWGN estimation

      preamble_peak(long peak_idx, float crosscorr_mag, float mag2, gr_complex acorr_val, float awgn_estim) :
        tidx(peak_idx),
        corr_mag(crosscorr_mag),
        preamble_mag2(mag2),
        autocorr_val(acorr_val),
        awgn_mag2(awgn_estim) {}
      inline float SNRdB() const {return 10*log10(snr());}
      inline float snr() const {return (preamble_mag2-awgn_mag2)/awgn_mag2;}
      inline float cfo() const {return compute_cfo(autocorr_val,1);}
    };

    class tracked_peak {
      preamble_peak c;
      double d_peak_idx;        //< time stamp where the preamble starts
    public:
      int n_frames_elapsed;
      int n_frames_detected;
      int n_missed_frames_contiguous;
      bool p_first_flag;

      enum TrackState {AWGN, CFO, TOFFSET};
      TrackState d_state;

      tracked_peak(long idx, float pcorr, float pmag2, gr_complex aval, float awgn_est);
      tracked_peak(const preamble_peak& p);
      void update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period);
      void update_cfo(gr_complex res);
      void update_awgn(float new_awgn);
      void update_mag2(float new_mag2);

      inline long preamble_idx() const { return c.tidx; }
      inline float crosscorr_mag() const { return c.corr_mag; }
      inline long increment_preamble_idx(long val) { d_peak_idx += val; c.tidx += val; }
      inline float preamble_power() const {return c.preamble_mag2;}
      inline float awgn_power() const {return c.awgn_mag2;}
      inline float cfo() const {return c.cfo();}
      inline float SNRdB() const {return 10*log10(c.snr());}
      inline float snr() const {return (c.preamble_mag2-c.awgn_mag2)/c.awgn_mag2;}
      inline preamble_peak peak_params() const {return c;}
    };

    tracked_peak::tracked_peak(long idx, float pcorr, float pmag2, gr_complex aval, float awgn_est) :
      c(idx, pcorr, pmag2, aval, awgn_est), 
      d_peak_idx((double)idx),
      n_frames_elapsed(0),
      n_frames_detected(0),
      n_missed_frames_contiguous(0),
      p_first_flag(true),
      d_state(tracked_peak::TOFFSET) {
    }

    tracked_peak::tracked_peak(const preamble_peak& p) :
      c(p), d_peak_idx(c.tidx),
      n_frames_elapsed(0),
      n_frames_detected(0),
      n_missed_frames_contiguous(0),
      p_first_flag(true),
      d_state(tracked_peak::TOFFSET) {
    }

    void tracked_peak::update_toffset(long new_peak, float corramp, float mag2, float thres, long frame_period) {
      if(corramp > thres) {
        if(p_first_flag==true) {
          c.corr_mag = corramp;
          c.preamble_mag2 = mag2;
          d_peak_idx = new_peak;
          p_first_flag = false;
          c.tidx = (long)round(d_peak_idx);
        }
        else {
          d_peak_idx = 0.95*d_peak_idx + 0.05*new_peak;
          c.tidx = (long)round(d_peak_idx);
          c.corr_mag = 0.95*c.corr_mag + 0.05*corramp;
          c.preamble_mag2 = 0.95*c.preamble_mag2 + 0.05*mag2;
        }
        n_frames_detected++;
        n_missed_frames_contiguous=0;
      }
      else {
        std::cout << "WARNING: The peak was missed. The crosscorr params were: {"
                  << new_peak << "," << corramp << "}"  << std::endl;
        n_missed_frames_contiguous++;
      }
      n_frames_elapsed++;
    }

    void tracked_peak::update_cfo(gr_complex res) {
      c.autocorr_val = 0.95f*c.autocorr_val + 0.05f*res;
      d_state = tracked_peak::TOFFSET;
    }

    void tracked_peak::update_awgn(float new_awgn) {
      c.awgn_mag2 = 0.95*c.awgn_mag2 + 0.05*new_awgn;
      d_state = tracked_peak::CFO;
    }

    void tracked_peak::update_mag2(float new_mag2) {
      c.preamble_mag2 = 0.95*c.preamble_mag2 + 0.05*new_mag2;
      d_state = tracked_peak::CFO;
    }

    std::string println(const preamble_peak& p) {
      std::stringstream ss;
      ss << "{" << p.tidx << "," << p.corr_mag << "," << p.preamble_mag2
         << "," << p.cfo() << "," << p.awgn_mag2 << "}";
      return ss.str();
    }

    std::string println(const tracked_peak& t) {
      std::stringstream ss;
      ss << "{" << println(t.peak_params()) << "," << t.n_frames_elapsed << "," << t.n_frames_detected << "}";
      return ss.str();
    }

    void fill_json_object(rapidjson::PrettyWriter<rapidjson::StringBuffer>& w, const preamble_peak& t) {
      w.String("idx");
      w.Int(t.tidx);
      w.String("corr_val");
      w.Double(t.corr_mag);
      w.String("peak_mag2");
      w.Double(t.preamble_mag2);
      w.String("schmidl_mean");
      w.String(print_complex(t.autocorr_val).c_str());
    }

  }
}

#endif
