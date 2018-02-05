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

from ..core.LuigiSimulatorHandler import *
from ..waveform_generators.waveform_generator_utils import SignalGenerator
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class waveform(StageLuigiTask):
    """
    This task generates waveform files
    """
    @staticmethod
    def depends_on():
        return None

    @staticmethod
    def setup():
        session_settings.global_settings['waveform_types'] = {}
        waveform_generators = SignalGenerator.__subclasses__()
        l = []
        for w in waveform_generators:
            session_settings.global_settings['waveform_types'][w.__name__] = w
            l.append(w.__name__)
        logger.info('These are the signal/waveform generators that were registered:{}'.format(l))

    def requires(self):
        return SessionInit(self.session_args)

    def run(self):
        logger.trace('Running Waveform Generator for %s',self.output().path)
        this_run_params = self.get_run_parameters()
        launch(this_run_params)

def launch(params):
    # TODO: use virtual function and map rather than elif
    wf = params['parameters']['waveform']
    if wf in ['square','saw']: #FIXME: It should not read the tag but the waveform parameter
        from . import signal_source as sc
        sc.run(params)
    elif wf=='wifi':
        from . import wifi_source as ws
        ws.run(params)
    elif wf=='generic_mod':
        from . import psk_source
        psk_source.run(params)
    elif wf=='lte':
        from . import lte_source
        lte_source.run(params)
    else:
        gen_name = params['parameters']['signal_generator']
        siggen = session_settings.global_settings['waveform_types'][gen_name]
        siggen.run(params)
    # else:
    #     raise ValueError('ERROR: Do not recognize this waveform')
