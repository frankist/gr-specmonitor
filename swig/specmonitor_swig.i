/* -*- c++ -*- */

#define SPECMONITOR_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "specmonitor_swig_doc.i"

%{
#include "specmonitor/framer_c.h"
//#include "specmonitor/corr_est_norm_cc.h"
#include "specmonitor/framer_snr_est_cc.h"
#include "specmonitor/spectrogram_img_c.h"
#include "specmonitor/random_burst_shaper_cc.h"
#include "specmonitor/hier_preamble_detector.h"
#include "specmonitor/foo_random_burst_shaper_cc.h"
#include "specmonitor/DynRandom.h"
//#include "specmonitor/frame_sync_cc.h"
%}


%include "specmonitor/framer_c.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, framer_c);
//%include "specmonitor/corr_est_norm_cc.h"
//GR_SWIG_BLOCK_MAGIC2(specmonitor, corr_est_norm_cc);
%include "specmonitor/framer_snr_est_cc.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, framer_snr_est_cc);
//%include "specmonitor/frame_sync_cc.h"
//GR_SWIG_BLOCK_MAGIC2(specmonitor, frame_sync_cc);
%include "specmonitor/spectrogram_img_c.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, spectrogram_img_c);
%include "specmonitor/random_burst_shaper_cc.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, random_burst_shaper_cc);
%include "specmonitor/hier_preamble_detector.h"
%include "specmonitor/foo_random_burst_shaper_cc.h"
GR_SWIG_BLOCK_MAGIC2(specmonitor, foo_random_burst_shaper_cc);
%include "specmonitor/DynRandom.h"
