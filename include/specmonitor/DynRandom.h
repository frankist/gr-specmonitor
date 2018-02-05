
#ifndef INCLUDED_SPECMONITOR_DYNRANDOM_H
#define INCLUDED_SPECMONITOR_DYNRANDOM_H

#include <specmonitor/api.h>
#include <string>
#include <vector>

namespace gr {
  namespace specmonitor {

    class DistInterface;

    /*!
     * \brief <+description+>
     *
     */
    class SPECMONITOR_API DynRandom
    {
    public:
      DynRandom(std::string dist_name, const std::vector<float>& params);
      ~DynRandom();
      float generate();
      std::vector<float> generate_N(int N);
    private:
      std::string d_dist_name;
      std::vector<float> d_params;

      DistInterface* d_rand_dist;
    };

  } // namespace specmonitor
} // namespace gr

#endif /* INCLUDED_SPECMONITOR_DYNRANDOM_H */

