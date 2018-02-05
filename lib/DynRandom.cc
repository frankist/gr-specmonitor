
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include <specmonitor/DynRandom.h>
#include "modules/dynrandom.h"

namespace gr {
  namespace specmonitor {

    DynRandom::DynRandom(std::string dist_name,
                         const std::vector<float>& params) :
      d_dist_name(dist_name),
      d_params(params),
      d_rand_dist(NULL)
    {
      // NOTE: Name convention equal to numpy or C++
      d_rand_dist = RegisteredDists::instance()->make_dist(d_dist_name,d_params);
    }

    DynRandom::~DynRandom()
    {
      if(d_rand_dist!=NULL)
        delete d_rand_dist;
    }

    float DynRandom::generate() {
      return d_rand_dist->generate();
    }

    std::vector<float> DynRandom::generate_N(int N) {
      std::vector<float> v(N);
      for(int i = 0; i < N; ++i)
        v[i] = generate();
      return v;
    }
  } /* namespace specmonitor */
} /* namespace gr */

