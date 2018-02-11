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

install(FILES
    specmonitor_framer_c.xml
    #specmonitor_corr_est_norm_cc.xml
    specmonitor_framer_snr_est_cc.xml
    #specmonitor_frame_sync_cc.xml
    specmonitor_darkflow_ckpt_classifier_c.xml
    specmonitor_spectrogram_img_c.xml
    specmonitor_darkflow_ckpt_classifier_msg.xml
    specmonitor_random_burst_shaper_cc.xml
    specmonitor_darkflow_statistics_collector.xml
    specmonitor_hier_preamble_detector.xml
    specmonitor_foo_random_burst_shaper_cc.xml
    specmonitor_DynRandom.xml DESTINATION share/gnuradio/grc/blocks
)
