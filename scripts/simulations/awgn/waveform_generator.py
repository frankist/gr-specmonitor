#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Francisco Paisana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

import sys
import MakeFileSimulator
sys.path.append('../../../python/modules')
sys.path.append('../../../python/modules/waveform_generators')
import signal_source as sc

def waveform_gen_launcher(params):
    if params['parameters']['waveform'] in ['square','saw']:
        sc.run_signal_source(params)
    else:
        raise ValueError('ERROR: Do not recognize this waveform')

