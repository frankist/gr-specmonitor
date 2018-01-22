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

import numpy as np
import pickle
import os
import luigi

from ..core import session_settings
from ..core import LuigiSimulatorHandler as lsh
from ..core import SessionParams as sp
from ..sig_format import sig_data_access as sda
from ..sig_format import pkl_sig_format
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class RemoveIQSamples(lsh.StageLuigiTask):
    completed = luigi.Parameter(significant=False,default=False)

    def stage2clean(self):
        raise NotImplementedError('This is an abstract class')

    @staticmethod
    def mkdir_flag():
        return False

    def requires(self):
        sessiondata = self.load_sessiondata()
        resulttasktuples = sessiondata.child_stage_idxs(self.stage2clean(),self.stage_idxs[0:-1])
        ret = []
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
        clean_IQ(this_run_params)
        self.completed = True

def IQcleaner_task_factory(classname,stage2clean):
    new_class = type(classname, # name of the new class
                     (RemoveIQSamples,), # base class
                     {"stage2clean": lambda self: stage2clean})
    return new_class

def register_IQcleaner_task_handler(stage2clean):
    class_name = '{}CleanIQ'.format(stage2clean)
    task = IQcleaner_task_factory(class_name,stage2clean)
    session_settings.register_task_handler(class_name,task)

# def ClassFactory(name, argnames, BaseClass=BaseClass):
#     def __init__(self, **kwargs):
#         for key, value in kwargs.items():
#             # here, the argnames variable is the one passed to the
#             # ClassFactory call
#             if key not in argnames:
#                 raise TypeError("Argument %s not valid for %s" 
#                     % (key, self.__class__.__name__))
#             setattr(self, key, value)
#         BaseClass.__init__(self, name[:-len("Class")])
#     newclass = type(name, (BaseClass,),{"__init__": __init__})
#     return newclass

def clean_IQ(args):
    # targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']

    ### get dependency file, and create a new stage_data object
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    if 'IQsamples' in freader.wavdata:
        del freader.wavdata['IQsamples']

    # clean original file
    with open(sourcefilename,'w') as f:
        pickle.dump(stage_data,f)
    # with open(targetfilename,'w') as f:
    #     f.write('success')
    logger.info('Finished cleaning up IQsamples in file %s',sourcefilename)
