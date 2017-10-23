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
import luigi
import itertools
import importlib
import session_params
import pickle

# This class is only to generate appropriate filename formats
class SessionFileNames:
    @staticmethod
    def stage_outputfile(session,stage,fidx_list):
        folder = '{}/{}/data_'.format(session,stage)
        filepath = folder + '_'.join([str(i) for i in fidx_list])
        return filepath+'.pkl'

    @staticmethod
    def session_pkl(params):
        session_name = params['session_name']
        return '{}/param_cfg.pkl'.format(session_name)

# this class stores data we pass through cmd line
# and identifies our session instance
class SessionInstanceParams:
    def __init__(self,session_name,cfg_file):
        self.session_name = session_name
        self.cfg_file = cfg_file

        self.session_path = './'+self.session_name

# this class stores the cmdline configuration of our session
# loads the config_file and stores its values
class LuigiSessionData:
    def __init__(self,cfg_params,session_params):
        self.cmd_cfg = cfg_params
        self.params = session_params

    def session_name(self):
        return self.cmd_cfg['session_name']

    def cfg_filename(self):
        return self.cmd_cfg['cfg_file']

    @classmethod
    def load_cfg_file(cls,sim_name,cfg_file):
        # Remove the extension and load the cfg_file
        fbase = os.path.splitext(os.path.basename(cfg_file))[0]
        try:
            cfg_module = importlib.import_module(fbase)
        except Exception, e:
            print 'Error while opening config file: ',str(e)
            exit(-1)
        # TODO: Parse the module to see if every variable is initialized
        sp = session_params.TaggedMultiStageParams(cfg_module.tags,
                                                   cfg_module.stage_names,
                                                   cfg_module.stage_params)
        return cls(sim_name,sp)

    @staticmethod
    def load_pkl(cfgparams):
        with open(SessionFileNames.session_pkl(cfgparams),'r') as f:
            return pickle.load(f)

# Luigi Tasks

# this task just verifies if the cfg file exists
class LuigiSessionCfgFile(luigi.ExternalTask):
    cfg_params = luigi.DictParameter()

    def output(self):
        return luigi.LocalTarget(self.cfg_params['cfg_file'])

class SessionInit(luigi.Task):
    cfg_params = luigi.DictParameter()

    def requires(self):
        return LuigiSessionCfgFile(self.cfg_params)

    def output(self):
        return luigi.LocalTarget(SessionFileNames.session_pkl(self.cfg_params))

    def run(self):
        # load the config file
        simdata = LuigiSessionData.load_cfg_file(self.cfg_params['session_name'],self.cfg_params['cfg_file'])

        # create folders for each stage
        def try_mkdir(name=None):
            fmt = '{}/{}'.format(self.cfg_params['session_name'],name) if name else self.cfg_params['session_name']
            if not os.path.exists(fmt):
                os.makedirs(fmt)
        try_mkdir()
        for s in simdata.params.stage_names:
            try_mkdir(s)

        # save the config file
        with self.output().open('wb') as f:
            pickle.dump(simdata,f)

class CmdSession(luigi.WrapperTask):
    cfg_params = luigi.DictParameter()
    stage_name = luigi.Parameter()

    def requires(self):
        assert self.stage_name is not None
        # run the session config setup as a sub-pipeline
        prerequisite = SessionInit(self.cfg_params)
        luigi.build([prerequisite], local_scheduler=True)

        # get itertools iterator of all possible idxs
        stage_idx_list = self.get_stage_idx_list()
        stage_task_caller = self.get_stage_caller()
        if not stage_task_caller:
            raise NotImplementedError('Method %s not implemented' % self.stage_name)

        # for each itertools product, call the LuigiTask
        return [stage_task_caller(self.cfg_params,list(s)) for s in stage_idx_list]

    def get_stage_idx_list(self):
        # get itertools iterator of all possible idxs
        simdata = LuigiSessionData.load_pkl(self.cfg_params)
        stage_lvl = simdata.params.stage_names.index(self.stage_name)
        stage_sizes = [simdata.params.length(stage=a) for a in range(stage_lvl+1)]
        stage_idx_list = itertools.product(*[range(s) for s in stage_sizes])
        return stage_idx_list

class StageLuigiTask(luigi.Task):
    cfg_params = luigi.DictParameter()
    stage_idxs = luigi.ListParameter()

    def output(self):
        filepath = SessionFileNames.stage_outputfile(self.cfg_params['session_name'],
                                               self.__class__.__name__,
                                               self.stage_idxs)
        # folder = '{}/{}'.format(self.cfg_params['session_name'],self.__class__.__name__)
        # filepath = '{}/data_{}_{}_{}.pkl'.format(folder,self.wav_idx,
        #                                          self.Tx_idx,self.RF_idx)
        return luigi.LocalTarget(filepath)

    def run(self):
        print 'do nothing'

# class LuigiSimDataLoader:
#     instance = None
#     def __init__(self,sim_name):
#         if not SimDataLoader.instance:
#             SimDataLoader.instance = LuigiSimData.load_pkl(sim_name)
#         else:
#             if sim_name!=LuigiSimData.session_name:
#                 SimDataLoader.instance = LuigiSimData.load_pkl(sim_name)
#     def __getattr__(self,name):
#         return getattr(self.instance,name)