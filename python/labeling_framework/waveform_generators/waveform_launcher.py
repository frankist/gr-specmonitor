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

from LuigiSimulatorHandler import *
import waveform_generator
import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class waveform(StageLuigiTask):
    """
    This task generates waveform files
    """
    def requires(self):
        return SessionInit(self.session_args)

    def run(self):
        logger.trace('Running Waveform Generator for %s',self.output().path)
        this_run_params = self.get_run_parameters()
        waveform_launcher(this_run_params)

def waveform_launcher(params):
    if params['parameters']['session_tag']=='sig_source': #FIXME: It should not read the tag but the waveform parameter
        import signal_source as sc
        sc.run_signal_source(params)
    elif params['parameters']['waveform']=='wifi':
        import wifi_source as ws
        ws.run(params)
    else:
        raise ValueError('ERROR: Do not recognize this waveform')
    pass