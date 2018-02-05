
#ifndef _QA_DYNRANDOM_H_
#define _QA_DYNRANDOM_H_

#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/TestCase.h>

namespace gr {
  namespace specmonitor {

    class qa_DynRandom : public CppUnit::TestCase
    {
    public:
      CPPUNIT_TEST_SUITE(qa_DynRandom);
      CPPUNIT_TEST(t1);
      CPPUNIT_TEST_SUITE_END();

    private:
      void t1();
    };

  } /* namespace specmonitor */
} /* namespace gr */

#endif /* _QA_DYNRANDOM_H_ */

