# Copyright 2011 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

########################################################################
# Include python install macros
########################################################################
include(GrPython)
if(NOT PYTHONINTERP_FOUND)
    return()
endif()

########################################################################
# Install python sources
########################################################################
GR_PYTHON_INSTALL(
    FILES
    __init__.py
    darkflow_ckpt_classifier_c.py
    darkflow_ckpt_classifier_msg.py DESTINATION ${GR_PYTHON_DIR}/specmonitor
)

########################################################################
# Handle subdirectories
########################################################################
add_subdirectory(darkflow_tools)
add_subdirectory(labeling_framework)

########################################################################
# Handle the unit tests
########################################################################
include(GrTest)

set(GR_TEST_TARGET_DEPS gnuradio-specmonitor)
set(GR_TEST_PYTHON_DIRS ${CMAKE_BINARY_DIR}/swig)
#GR_ADD_TEST(qa_framer_c ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_framer_c.py)
##GR_ADD_TEST(qa_corr_est_norm_cc ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_corr_est_norm_cc.py)
#GR_ADD_TEST(qa_framer_snr_est_cc ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_framer_snr_est_cc.py)
#GR_ADD_TEST(qa_frame_sync_cc ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_frame_sync_cc.py)
GR_ADD_TEST(qa_darkflow_ckpt_classifier_c ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_darkflow_ckpt_classifier_c.py)
add_subdirectory(tests)

GR_ADD_TEST(qa_spectrogram_img_c ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_spectrogram_img_c.py)
GR_ADD_TEST(qa_darkflow_ckpt_classifier_msg ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/qa_darkflow_ckpt_classifier_msg.py)
