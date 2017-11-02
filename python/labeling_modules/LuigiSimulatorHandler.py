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

import os
import sys
import luigi
import itertools
import importlib
import pickle
import logging
sys.path.append(os.path.abspath('../utils'))
import SessionParams as sp
import StageParamData
from basic_utils import *

# This class is only to generate appropriate filename formats


class SessionFileNames:
    @staticmethod
    def stage_outputfile(session, stage, fidx_list):
        folder = '{}/{}/data_'.format(session, stage)
        filepath = folder + '_'.join([str(i) for i in fidx_list])
        return filepath + '.pkl'

    @staticmethod
    def session_pkl(params):
        session_name = params['session_name']
        return '{}/param_cfg.pkl'.format(session_name)

# this class stores data we pass through cmd line
# and identifies our session instance


class SessionInstanceParams:
    def __init__(self, session_name, cfg_file):
        self.session_name = session_name
        self.cfg_file = cfg_file

        self.session_path = './' + self.session_name

# this class stores the cmdline configuration of our session
# loads the config_file and stores its values
# class LuigiSessionData:
#     def __init__(self,session_args,session_args):
#         self.cmd_cfg = session_args
#         self.params = session_args

#     def session_name(self):
#         return self.cmd_cfg['session_name']

#     def cfg_filename(self):
#         return self.cmd_cfg['cfg_file']

#     @classmethod
#     def load_cfg_file(cls,sim_name,cfg_file):
#         if not os.path.isfile(cfg_file):
#             logging.error('The provided config file %s does not seem to exist',cfg_file)
#             exit(-1)
#         # Remove the extension and load the cfg_file
#         fbase = os.path.splitext(os.path.basename(cfg_file))[0]
#         logging.info('Going to load config file %s',fbase)
#         try:
#             cfg_module = importlib.import_module(fbase)
#         except Exception, e:
#             logging.error('Could not open config file: ',str(e))
#             exit(-1)
#         # TODO: Parse the module to see if every variable is initialized
#         sp = session_args.TaggedMultiStageParams(cfg_module.tags,
#                                                    cfg_module.stage_names,
#                                                    cfg_module.stage_params)
#         return cls(sim_name,sp)

#     @staticmethod
#     def load_pkl(cfgparams):
#         with open(SessionFileNames.session_pkl(cfgparams),'r') as f:
#             return pickle.load(f)

# Luigi Tasks

# this task just verifies if the cfg file exists


class LuigiSessionCfgFile(luigi.ExternalTask):
    session_args = luigi.DictParameter()  # {'session_path':x,'cfg_file':y}

    def output(self):
        return luigi.LocalTarget(self.session_args['cfg_file'])


class SessionInit(luigi.Task):
    session_args = luigi.DictParameter()

    def get_arg_obj(self):
        return sp.SessionInstanceArguments.load_dict(self.session_args)

    def requires(self):
        return LuigiSessionCfgFile(self.session_args)

    def output(self):
        session_arg_obj = self.get_arg_obj()
        return luigi.LocalTarget(sp.SessionPaths.session_pkl(session_arg_obj))

    def complete(self):
        import luigi_utils
        return luigi_utils.check_complete_with_date(self)

    def run(self):
        # loads config file
        # setups the folders
        # setups remote folders
        # saves pkl with params
        session_arg_obj = self.get_arg_obj()
        sp.session_init(session_arg_obj)
        # # load the config file
        # simdata = LuigiSessionData.load_cfg_file(self.session_args['session_name'],self.session_args['cfg_file'])

        # # create folders for each stage
        # def try_mkdir(name=None):
        #     fmt = '{}/{}'.format(self.session_args['session_name'],name) if name else self.session_args['session_name']
        #     if not os.path.exists(fmt):
        #         os.makedirs(fmt)
        # try_mkdir()
        # for s in simdata.params.stage_names:
        #     try_mkdir(s)

        # # save the config file
        # with self.output().open('wb') as f:
        #     pickle.dump(simdata,f)


class CmdSession(luigi.WrapperTask):
    session_path = luigi.Parameter()
    cfg_file = luigi.Parameter()
    stages_to_run = luigi.Parameter()
    clean_first = luigi.Parameter(significant=False,default='False')
    first_run = luigi.Parameter(significant=False,default='True')

    def session_args(self):
        # NOTE: This was originally a DictParameter()
        # but it is a pain to define dicts in the command line
        # since luigi removes the ""
        return {'session_path':self.session_path,'cfg_file':self.cfg_file}

    def requires(self):
        if self.first_run=='True':
            self.first_run='False'
            if self.clean_first=='True':
                sp.session_clean(self.session_args())
            # run the session config setup as a sub-pipeline
            prerequisite = SessionInit(self.session_args())
            luigi.build([prerequisite], local_scheduler=True)

        # get itertools iterator of all possible idxs
        sessiondata = sp.load_session(self.session_args())
        stage_list = force_iterable_not_str(self.stages_to_run)
        callers = []
        for s in stage_list:
            callers += self.get_luigi_callers(sessiondata, s)
        return callers

    # creates a list of callers respective to stage given as argument
    # each caller corresponds to a different iteration of stage parameters
    def get_luigi_callers(self, sessiondata, stage):
        stage_idx_list = sessiondata.get_stage_iteration_indices(stage)
        stage_task_caller = self.get_stage_caller(stage)
        if not stage_task_caller:
            logging.error('Method %s not implemented', stage)
            raise NotImplementedError('Method %s not implemented' % stage)
        return [stage_task_caller(self.session_args(), idxs) for idxs in list(stage_idx_list)]

class StageLuigiTask(luigi.Task):
    session_args = luigi.DictParameter()
    stage_idxs = luigi.ListParameter()

    def load_sessiondata(self):
        return sp.load_session(self.session_args)

    def my_stage_name(self):
        return self.__class__.__name__

    def output(self):
        stage_name = self.my_stage_name()
        outfilename = sp.SessionPaths.stage_outputfile(self.session_args['session_path'],
                                         stage_name,
                                         self.stage_idxs)
        # filepath = SessionFileNames.stage_outputfile(self.session_args['session_path'],
        #                                        stage_name,
        #                                        self.stage_idxs)
        # folder = '{}/{}'.format(self.session_args['session_name'],self.__class__.__name__)
        # filepath = '{}/data_{}_{}_{}.pkl'.format(folder,self.wav_idx,
        #                                          self.Tx_idx,self.RF_idx)
        return luigi.LocalTarget(outfilename)

    def get_run_parameters(self):
        sessiondata = self.load_sessiondata()
        this_stage = self.my_stage_name()
        iterable_parameters = sessiondata.get_run_parameters(this_stage,self.stage_idxs)
        outputfile = self.output().path
        parent_stage = sessiondata.stage_dependency_tree.get_stage_dependency(this_stage)
        d = {'parameters':dict(iterable_parameters),
        'targetfolder':os.path.dirname(outputfile),
        'targetfilename':outputfile,
        'sourcefilename':self.requires().output().path,
        'stage_name':this_stage,
        'previous_stage_name':parent_stage}
        return d

    def run(self):
        print 'do nothing'
