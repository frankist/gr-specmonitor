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

import luigi

from ..core import SignalDataFormat as ssa
from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..core import SessionParams as sp
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

# import os
# import numpy as np
# def get_folder_size(folder):
#     total_size = os.path.getsize(folder)
#     for item in os.listdir(folder):
#         itempath = os.path.join(folder, item)
#         if os.path.isfile(itempath):
#             total_size += os.path.getsize(itempath)
#         elif os.path.isdir(itempath):
#             total_size += get_folder_size(itempath)
#     return total_size

class RemoveIQSamples(StageLuigiTask):
    completed = luigi.BoolParameter(significant=False,default=False)
    # @property
    # def priority(self):
    #     req = super(RemoveIQSamples,self).requires()
    #     logger.info('My requirement is {}. Is it complete? {}'.format(req,req.complete()))
    #     if req.complete():
    #         return 1000
    #     return 0
    #     # session_path = os.path.abspath(sp.SessionPaths.session_folder(self.session_args))
    #     # stage_dirs = [f for f in os.listdir(session_path) if os.path.isdir(os.path.join(session_path,f)) and f!='tmp']
    #     # logger.info('These are the stage dirs:{}'.format(stage_dirs))
    #     # if len(stage_dirs)==0:
    #     #     return 0
    #     # # logger.info('These are the folders: {}'.format(stage_dirs))
    #     # folder_sizes = [get_folder_size(os.path.join(session_path,d)) for d in stage_dirs]
    #     # logger.info('These are the folder sizes: {}'.format(folder_sizes))
    #     # max_idx = np.argmax(folder_sizes)
    #     # logger.info('I am {}'.format(self.depends_on()))
    #     # if self.depends_on()==stage_dirs[max_idx]:
    #     #     logger.info('I am {} cleaner and this is the folder with max size of {}.'.format(self.depends_on(),folder_sizes[max_idx]))
    #     #     return 1000
    #     # return 0

    @staticmethod
    def mkdir_flag():
        return False

    def stage2clean(self):
        if isinstance(self.depends_on(),basestring):
            return self.depends_on()
        return self.depends_on().my_task_name()

    def requires(self):
        ret = super(RemoveIQSamples,self).requires()
        if not isinstance(ret,list):
            ret = [ret]
        sessiondata = self.load_sessiondata()
        resulttasktuples = sessiondata.child_stage_idxs(self.stage2clean(),self.stage_idxs[0:-1])
        for taskhandler,child_stage_idx_list in resulttasktuples.items():
            if taskhandler.__name__ == self.my_task_name():
                continue
            for child_stage_idxs in child_stage_idx_list:
                task_instance = taskhandler(self.session_args, child_stage_idxs)
                ret.append(task_instance)
        return ret

    def stage2clean_output(self):
        outfilename = sp.SessionPaths.stage_outputfile(self.session_args['session_path'],
                                         self.stage2clean(),
                                         self.stage_idxs[0:-1],self.output_fmt)
        return outfilename

    def output(self):
        return []
    #     file2clean = self.stage2clean_output()
    #     a = os.path.splitext(file2clean)
    #     cleanup_marker_file = '{}_cleaned.txt'.format(a[0])
    #     return luigi.LocalTarget(cleanup_marker_file)

    def complete(self):
        return self.completed

    def get_run_parameters(self):
        file2clean = self.stage2clean_output()
        # outputfile = self.output().path
        d = {'targetfilename':None,#outputfile,
             'sourcefilename':file2clean}
        return d

    def run(self):
        this_run_params = self.get_run_parameters()
        # logger.info('Going to clean IQ samples of {}'.format(this_run_params['sourcefilename']))
        clean_IQ(this_run_params)
        self.completed = True

def clean_IQ(args):
    # targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']

    ### get dependency file, and create a new stage_data object
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(args)
    multi_stage_data.clean_previous_samples()
    multi_stage_data.save_pkl()
