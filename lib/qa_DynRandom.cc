#include <gnuradio/attributes.h>
#include <cppunit/TestAssert.h>
#include "qa_DynRandom.h"
#include <specmonitor/DynRandom.h>
#include <algorithm>

namespace gr {
  namespace specmonitor {

    void
    qa_DynRandom::t1()
    {
      std::vector<float> params(2);
      params[0] = 1;
      params[1] = 10;
      // Put test here
      DynRandom d = DynRandom("randint",params);
      for(int i = 0; i < 10; ++i){
        float ret = d.generate();
        CPPUNIT_ASSERT(ret<=params[1] and ret>=params[0]);
      }
      std::vector<float> vals = d.generate_N(100);
      float max_val = *std::max_element(vals.begin(),vals.end());
      float min_val = *std::min_element(vals.begin(),vals.end());
      CPPUNIT_ASSERT(max_val>=params[0] and max_val<=params[1]);
      CPPUNIT_ASSERT(min_val>=params[0] and min_val<=params[1]);
      CPPUNIT_ASSERT(max_val>min_val);

      params.pop_back();
      DynRandom d2 = DynRandom("constant",params);
      std::vector<float> vals2 = d2.generate_N(100);
      for(int i = 0; i < vals2.size(); ++i) {
        CPPUNIT_ASSERT(vals2[i]==params[0]);
      }
    }

  } /* namespace specmonitor */
} /* namespace gr */

