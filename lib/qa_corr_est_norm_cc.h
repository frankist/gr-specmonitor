/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

/* 
 * File:   qa_corr_est_norm_cc_impl.h
 * Author: xico
 *
 * Created on 03 July 2017, 15:02
 */

#ifndef _QA_CORR_EST_NORM_CC_H_
#define _QA_CORR_EST_NORM_CC_H_

#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/TestCase.h>

namespace gr {
  namespace specmonitor {

    class qa_corr_est_norm_cc : public CppUnit::TestCase
    {
    public:
      CPPUNIT_TEST_SUITE(qa_corr_est_norm_cc);
      CPPUNIT_TEST(t1);
      CPPUNIT_TEST_SUITE_END();

    private:
      void t1();
    };

  } /* namespace specmonitor */
} /* namespace gr */

#endif /* QA_CORR_EST_NORM_CC_H_ */

