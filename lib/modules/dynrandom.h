#ifndef DYNRANDOM_H
#define DYNRANDOM_H

#include <ctime>
#include <cassert>
#include <map>
#include <string>
#include <vector>
#include <boost/random.hpp>
#include <boost/function.hpp>
#include <iostream>
#include <sstream>

namespace gr {
  namespace specmonitor {
    // specify types
    class DistInterface;
    typedef const std::vector<float>& param_format;
    typedef boost::function<DistInterface*(param_format)> factory_type;

    // This is an abstract class
    class DistInterface {
    private:
      DistInterface(const DistInterface& d);
    public:
      DistInterface() {}
      virtual float generate() = 0;
      virtual ~DistInterface(){}
    };

    void call_exception_args(int val,int expected) {
      if(val==expected)
        return;
      std::stringstream ss;
      ss << "ERROR: This distribution expects " << expected << " parameters. However it got " << val;
      std::cerr << ss.str() << std::endl;
      throw std::invalid_argument(ss.str());
    }

    // Uniform Int Distribution

    class RandIntDist : public DistInterface {
      boost::random::mt19937 d_rng;
      boost::random::uniform_int_distribution<> d_dist;
    public:
      RandIntDist(int left, int right) :
        d_rng(static_cast<unsigned int>(std::time(0))),
        d_dist(left,right) {
      }
      virtual float generate() {
        return d_dist(d_rng);
      }
      int min() const {return d_dist.min();}
      int max() const {return d_dist.max();}
      static DistInterface* pymake(const std::vector<float>& params) {
        call_exception_args(params.size(),2);
        return new RandIntDist((int)params[0],(int)params[1]);
      }
    };

    // Constant Distribution
    class ConstantDist : public DistInterface {
      float d_val;
    public:
      ConstantDist(float v) : d_val(v) {}
      virtual float generate() {return d_val;}
      static DistInterface* pymake(const std::vector<float>& params) {
        call_exception_args(params.size(),1);
        return new ConstantDist(params[0]);
      }
    };

    class RegisteredDists {
    private:
      std::map<std::string,factory_type> dist_map;
      typedef std::map<std::string, factory_type>::iterator iterator;
      static RegisteredDists* s_instance;
      RegisteredDists();
    public:
      DistInterface* make_dist(std::string name,
                                      const std::vector<float>& p) {
        RegisteredDists::iterator it = dist_map.find(name);
        if(it==dist_map.end()) {
          std::stringstream ss;
          ss << "ERROR: The distribution \"" << name << "\" has not been registered yet.";
          std::cerr << ss.str() << std::endl;
          throw std::invalid_argument(ss.str());
        }
        return it->second(p);
      }
      void register_dist(std::string name,
                                const factory_type fptr) {
        dist_map.insert(make_pair(name,fptr));
      }

      static RegisteredDists* instance() {
        if(s_instance==NULL)
          s_instance = new RegisteredDists();
        return s_instance;
      }
    };

    RegisteredDists *RegisteredDists::s_instance = NULL;

    RegisteredDists::RegisteredDists() {
      // register known distributions
      register_dist("randint",&RandIntDist::pymake);
      register_dist("constant",&ConstantDist::pymake);
    }
  }
}
#endif
