#ifndef SPECMONITOR_RANDOM_H_
#define SPECMONITOR_RANDOM_H_

// This code creates several distributions that can be called dynamically(polymorphic).

#include <iostream>
#include <boost/random.hpp>

namespace gr {
  namespace specmonitor {

    // base class
    struct DistAbstract {
      unsigned int seed;
      boost::random::mt19937 rng;
      DistAbstract() : seed(static_cast<unsigned int>(std::time(0))), rng(seed)
      {}
      virtual int gen() = 0;
    };

    // uniform int
    struct UniformIntDist : public DistAbstract {
      boost::random::uniform_int_distribution<> d_dist;
      UniformIntDist(int left, int right) : d_dist(left,right) {}
      int gen() {
        return d_dist(rng);
      }
    };

    // constant
    struct ConstantValue : public DistAbstract {
      int d_val;
      ConstantValue(int val) : d_val(val) {}
      int gen() {
        return d_val;
      }
    };

    struct PoissonDist : public DistAbstract {
      boost::random::poisson_distribution<> d_dist;
      int d_offset;
      int d_upper_limit;
      PoissonDist(int mean,
                  int offset=0,
                  int upper_limit = std::numeric_limits<int>::max()) :
        d_dist(mean),
        d_offset(offset),
        d_upper_limit(upper_limit) {}
      int gen() {
        return std::min(d_offset+d_dist(rng),d_upper_limit);
      }
    };

    DistAbstract* distribution_factory(std::string distname, const std::vector<float>& params) {
      int param_idx = 0;
      DistAbstract* ret;
      if(distname=="poisson") {
        switch(params.size()) {
        case 1:
          ret = new PoissonDist(params[param_idx++]);
          break;
        case 2:
          ret = new PoissonDist(params[param_idx++],params[param_idx++]);
          break;
        case 3:
          ret = new PoissonDist(params[param_idx++],params[param_idx++],params[param_idx++]);
          break;
        default:
          std::stringstream ss;
          ss << "Invalid number of parameters (";
          ss << params.size();
          ss << ") for the distribution";
          throw std::invalid_argument(ss.str());
        }
      }
      else if(distname=="uniform") {
        if(params.size()!=2)
          throw std::invalid_argument("Invalid number of parameters for the distribution");
        ret = new UniformIntDist(params[0],params[1]);
        param_idx+=2;
      }
      else if(distname=="constant") {
        if (params.size()!=1)
          throw std::invalid_argument("Invalid number of parameters for the distribution");
        ret = new ConstantValue(params[0]);
        param_idx++;
      }
      else {
        std::string errmsg = "I do not recognise the distribution \"" + distname + "\n";
        throw std::invalid_argument(errmsg);
      }

      return ret;
    }
  }
}
#endif
