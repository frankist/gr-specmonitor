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

import labeling_framework as lf
from labeling_framework.core import LuigiSimulatorHandler as lsh
logger = lf.DynamicLogger(__name__)

class SignalGenerator(object):
    @staticmethod
    def run(params):
        raise NotImplemented('This is an abstract method')

class waveform(lf.StageLuigiTask):
    """
    This task generates waveform files
    """
    @staticmethod
    def depends_on():
        return None

    @staticmethod
    def setup():
        lf.session_settings.global_settings['waveform_types'] = {}
        waveform_generators = SignalGenerator.__subclasses__()
        l = []
        for w in waveform_generators:
            if w.name() in lf.session_settings.global_settings['waveform_types']:
                raise AssertionError('The waveform with name {} is a duplicate.'.format(w.name()))
            lf.session_settings.global_settings['waveform_types'][w.name()] = w
            l.append(w.name())
        logger.info('These are the signal/waveform generators that were registered:{}'.format(l))

    def requires(self):
        return lsh.SessionInit(self.session_args)

    def run(self):
        logger.trace('Running Waveform Generator for %s',self.output().path)
        this_run_params = self.get_run_parameters()

        # delegate to the correct waveform generator
        waveform_name = this_run_params['parameters']['waveform']
        wav_generator = lf.session_settings.global_settings['waveform_types'].get(waveform_name,None)
        if wav_generator is not None:
            wav_generator.run(this_run_params)
        else:
            raise ValueError('ERROR: Do not recognize this waveform')
