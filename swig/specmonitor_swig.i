/* -*- c++ -*- */

#define SPECMONITOR_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "specmonitor_swig_doc.i"

%{
#include "specmonitor/framer_c.h"
#include "specmonitor/corr_est_norm_cc.h"
#include "specmonitor/framer_snr_est_cc.h"
%}


%include "specmonitor/framer_c.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, framer_c);
%include "specmonitor/corr_est_norm_cc.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, corr_est_norm_cc);
%include "specmonitor/framer_snr_est_cc.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, framer_snr_est_cc);
