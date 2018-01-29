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

import json
import jsonpickle
import matplotlib.pyplot as plt

from ..labeling_tools import bounding_box
from ..sig_format import stage_signal_data as ssa
from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..utils import typesystem_utils as ts
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def write_metadata_to_json(this_run_params):
    targetfile = this_run_params['targetfilename']
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(this_run_params)
    multi_stage_data.clean_previous_samples() # need to clean IQsamples
    d = multi_stage_data
    # sig_data = freader.data()
    # sig_params = sig_data['parameters']
    # sig_derived_params = sig_data['derived_parameters']

    # d = {'parameters':ts.np_to_native(sig_params),'derived_parameters':ts.np_to_native(sig_derived_params)}
    with open(targetfile,'w') as f:
        js = jsonpickle.encode(d,unpicklable=False)
        jsident = json.dumps(json.loads(js), indent=2) # unfortunately i can't specify indent in jsonpickle
        f.write(jsident)

class Labels2JsonTask(StageLuigiTask):
    def __init__(self,*args,**kwargs):
        kwargs['output_fmt'] = '.json'
        super(Labels2JsonTask,self).__init__(*args,**kwargs)

    def run(self):
        this_run_params = self.get_run_parameters()
        write_metadata_to_json(this_run_params)
