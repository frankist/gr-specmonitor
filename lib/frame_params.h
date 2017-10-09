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
#include "utils/serialization/rapidjson/document.h"

#ifndef _FRAME_PARAMS_H_
#define _FRAME_PARAMS_H_

namespace gr {
  namespace specmonitor {

    // class preamble_params {
    //   std::vector<volk_utils::volk_array<gr_complex> > pseq_list;
    //   std::vector<size_t> pseq_sequence;

    // }

    class frame_params {
    public:
      std::vector<volk_utils::volk_array<gr_complex> > pseq_vec;
      std::vector<size_t> len;
      std::vector<int> n_repeats;
      long frame_period;
      int awgn_len;
      int guard_duration;
      // int frame_seqno_size;

      frame_params(const std::vector<std::vector<gr_complex> >& p_vec, const std::vector<int>& n_r,
                   long f_period, int awgn_l, int g_period) : //, int n_pseq) :
        pseq_vec(p_vec.size()),
        len(p_vec.size()),
        n_repeats(n_r),
        frame_period(f_period),
        awgn_len(awgn_l),
        guard_duration(g_period) {
        // frame_seqno_size(n_pseq) {
        assert(pseq_vec.size()==n_r.size());
        for(int i = 0; i < p_vec.size(); ++i) {
          len[i] = p_vec[i].size();
          // pseq_vec[i] = (gr_complex*) volk_malloc(sizeof(gr_complex)*len[i], volk_get_alignment());
          pseq_vec[i].resize(len[i]);
          std::copy(&p_vec[i][0], &p_vec[i][len[i]], &pseq_vec[i][0]);
          utils::normalize(&pseq_vec[i][0], len[i]);
        }
      }

      int preamble_duration() const {
        int sum = 0;
        for(int i = 0; i < len.size(); ++i)
          sum += len[i]*n_repeats[i];
        return sum;
      }

    // private:
      // frame_params(const frame_params& f) {} // deleted
      // frame_params& operator=(const frame_params& f) {} // deleted
    };

    namespace frame_params_utils {
      void compute_preamble(volk_utils::volk_array<gr_complex> &out, const frame_params& f) {
        out.resize(f.preamble_duration());
        int n = 0;
        for(int i = 0; i < f.len.size(); ++i)
          for(int r = 0; r < f.n_repeats[i]; ++r) {
            std::copy(&f.pseq_vec[i][0], &f.pseq_vec[i][f.len[i]], &out[n]);
            utils::set_mean_amplitude(&out[n],f.len[i]);
            n += f.len[i];
          }
        utils::normalize(&out[0],f.preamble_duration());
      }

      frame_params parse_json(const std::string& j) {
        using namespace rapidjson;
        Document d;
        d.Parse(j.c_str());

        assert(d.HasMember("n_repeats"));
        const Value& a = d["n_repeats"];
        assert(a.IsArray());
        std::vector<int> n_r(a.Size());
        for(int i = 0; i < a.Size(); ++i)
          n_r[i] = a[i].GetInt();

        assert(d.HasMember("pseq_vec"));
        const Value& b = d["pseq_vec"];
        assert(b.IsArray());
        std::vector<std::vector<gr_complex > > p_vec(b.Size());
        for(int i = 0; i < b.Size(); ++i) {
          assert(b[i].IsArray());
          const Value& t = b[i];
          p_vec[i].resize(t.Size());
          for(int j = 0; j < t.Size(); ++j) {
            assert(t[j].Size()==2);
            p_vec[i][j] = std::complex<float>(t[j][0].GetDouble(),t[j][1].GetDouble());//utils::parse_complex<float>(t[j].GetString());
          }
        }

        assert(d.HasMember("frame_period"));
        assert(d["frame_period"].IsInt());
        long f_period = d["frame_period"].GetInt();

        assert(d.HasMember("awgn_len"));
        assert(d["awgn_len"].IsInt());
        int awgn_len = d["awgn_len"].GetInt();

        assert(d.HasMember("guard_duration"));
        assert(d["guard_duration"].IsInt());
        int guard_duration = d["guard_duration"].GetInt();

        return frame_params(p_vec, n_r, f_period, awgn_len, guard_duration);
      }
    };
  }
}

#endif
