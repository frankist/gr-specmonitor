# Copyright 2011,2012,2016 Free Software Foundation, Inc.
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
# Setup library
########################################################################
include(GrPlatform) #define LIB_SUFFIX

include_directories(${Boost_INCLUDE_DIR})
link_directories(${Boost_LIBRARY_DIRS})

list(APPEND specmonitor_sources
    framer_c_impl.cc
    #corr_est_norm_cc_impl.cc
    framer_snr_est_cc_impl.cc
    #frame_sync_cc_impl.cc
    spectrogram_img_c_impl.cc
    random_burst_shaper_cc_impl.cc
    hier_preamble_detector.cc
    foo_random_burst_shaper_cc_impl.cc )

set(specmonitor_sources "${specmonitor_sources}" PARENT_SCOPE)
if(NOT specmonitor_sources)
	MESSAGE(STATUS "No C++ sources... skipping lib/")
	return()
endif(NOT specmonitor_sources)

add_library(gnuradio-specmonitor SHARED ${specmonitor_sources})
target_link_libraries(gnuradio-specmonitor ${Boost_LIBRARIES} ${GNURADIO_ALL_LIBRARIES} gnuradio-filter gnuradio-blocks)
set_target_properties(gnuradio-specmonitor PROPERTIES DEFINE_SYMBOL "gnuradio_specmonitor_EXPORTS")

if(APPLE)
    set_target_properties(gnuradio-specmonitor PROPERTIES
        INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
    )
endif(APPLE)

########################################################################
# Install built library files
########################################################################
include(GrMiscUtils)
GR_LIBRARY_FOO(gnuradio-specmonitor RUNTIME_COMPONENT "specmonitor_runtime" DEVEL_COMPONENT "specmonitor_devel")

########################################################################
# Build and register unit test
########################################################################
include(GrTest)

include_directories(${CPPUNIT_INCLUDE_DIRS})

list(APPEND test_specmonitor_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/test_specmonitor.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/qa_specmonitor.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/qa_hier_preamble_detector.cc
#    ${CMAKE_CURRENT_SOURCE_DIR}/qa_frame_sync_cc.cc
    ${CMAKE_CURRENT_SOURCE_DIR}/qa_framer_c.cc
    #${CMAKE_CURRENT_SOURCE_DIR}/qa_corr_est_norm_cc.cc
)

add_executable(test-specmonitor ${test_specmonitor_sources})

target_link_libraries(
  test-specmonitor
  ${GNURADIO_RUNTIME_LIBRARIES}
  ${Boost_LIBRARIES}
  ${CPPUNIT_LIBRARIES}
  volk
  gnuradio-specmonitor
)

GR_ADD_TEST(test_specmonitor test-specmonitor)

########################################################################
# Print summary
########################################################################
message(STATUS "Using install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "Building for version: ${VERSION} / ${LIBVER}")

