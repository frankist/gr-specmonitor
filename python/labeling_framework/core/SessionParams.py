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
import importlib
import pickle
# import itertools

import labeling_framework as lf
from . import StageParamData
from . import StageDependencyTree as sdt
from ..utils import ssh_utils
from ..utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

# this class stores all the data necessary to setup a session instance
# - It needs to specify our instance name (e.g. 'sim0')
# - The path to the cfg file where stage params and dependencies are provided
# - The hosts in case we are going to set remote connections
# - It can be loaded from the command line by passing a dictionary
class SessionInstanceArguments:
    def __init__(self,sessionabspath,cfg_file):
        self.sessionabspath = os.path.abspath(sessionabspath)
        self.session_name = os.path.basename(sessionabspath)
        self.cfg_filename = cfg_file
    
    def session_path(self):
        return self.sessionabspath
    
    def session_config_file(self):
        return self.cfg_filename

    def todict(self):
        return {'session_path':self.sessionabspath,'cfg_file':self.cfg_filename}

    @classmethod
    def load_dict(cls,d):
        return cls(d['session_path'],d['cfg_file'])

class SessionData:
    def __init__(self,session_instance_args,stage_params,stage_dependency_tree,ssh_hosts):
        self.session_args = session_instance_args
        self.stage_params = stage_params # session_params.TaggedMultiStageParams type
        self.stage_dependency_tree = stage_dependency_tree
        self.ssh_hosts = ssh_hosts

    def args(self):
        return self.session_args

    def remote_exists(self):
        return self.ssh_hosts is not None and len(self.ssh_hosts)>0

    def stage_name_list(self):
        return self.stage_dependency_tree.stage_names

    def get_session_idx_tuples(self,stage_name):
        """
        Returns a iterator (itertools) that goes from (0,0,...,0),(0,0,...,1),...,(4,3,...,6)
        Basically iterates over all file indices from the first stage up to "stage_name"
        """
        return StageParamData.generate_session_run_idxs(self.stage_params,stage_name)
        # dep_path = self.stage_dependency_tree.stage_dep_path[stage_name]
        # dep_len_list = [self.stage_params.length(stage=s) for s in reversed(dep_path)]
        # stage_idx_list = itertools.product(*[range(s) for s in dep_len_list])
        # return stage_idx_list

    def get_run_parameters(self,stage_name,stage_idx_tuple):
        return StageParamData.get_run_parameters(self.stage_params,stage_idx_tuple,stage_name)
        # this_stage_param_idx = stage_idx_tuple[-1]
        # tag = self.stage_params.get_tag_name(stage_idx_tuple)
        # return list(self.stage_params.get_stage_iterable(stage=stage_name,tag=tag,this_stage_param_idx))[0]

    def hosts(self):
        return self.ssh_hosts

    def child_stage_idxs(self,stage_name,this_stage_idxs=None):
        child_tasks = self.stage_dependency_tree.get_stage_childs(stage_name)
        l = {}
        for c in child_tasks:
            taskhandler = lf.session_settings.retrieve_task_handler(c)
            if this_stage_idxs is None:
                l[taskhandler] = [stage_idxs for stage_idxs in self.get_session_idx_tuples(c)]
            else:
                l[taskhandler] = [stage_idxs for stage_idxs in self.get_session_idx_tuples(c) if tuple(this_stage_idxs)==stage_idxs[0:-1]]
                # idxs_list = self.get_session_idx_tuples(c)
            # for stage_idxs in idxs_list:
            #     taskinstance=taskhandler(self.session_args.todict(), stage_idxs)
            #     print 'this is the output:',taskinstance.output().path
            #     l.append(taskinstance.output().path)
            #     # l.append(SessionPaths.stage_outputfile(self.stage_params, c, stage_idxs,taskhandler.output_fmt))
        return l

    @classmethod
    def load_cfg(cls,session_args):
        cfg_file = session_args.session_config_file()
        # Remove the extension and load the cfg_file
        fbase = os.path.splitext(os.path.basename(cfg_file))[0]
        try:
            cfg_module = importlib.import_module(fbase) # TODO: Find an appropriate format that is not a python file load
        except ImportError, e:
            err_str = 'Could not load the config file {}:{}'.format(cfg_file,str(e))
            logger.error(err_str)
            raise ImportError(err_str)
        # TODO: Parse the module to see if every variable is initialized
        deptree = sdt.StageDependencyTree(lf.session_settings.get_task_dependency_tree())#cfg_module.stage_dependency_tree)
        sp = StageParamData.TaggedMultiStageParams(cfg_module.tags,
                                                   deptree,
                                                   cfg_module.stage_params)
        hosts = cfg_module.ssh_hosts if hasattr(cfg_module,'ssh_hosts') else None
        return cls(session_args,sp,deptree,hosts)

# This class is only an interface to generate appropriate folder paths, and filename formats
# This way i separate the concerns of each class and I have one single point where I make changes to the file/folder names
class SessionPaths:
    @staticmethod
    def __session_args__(data): # receives or either sessioninstancearguments or sessiondata
        if isinstance(data,SessionInstanceArguments):
            return data
        elif isinstance(data,SessionData):
            return data.args()
        return SessionInstanceArguments.load_dict(data)

    @staticmethod
    def session_folder(data):
        return SessionPaths.__session_args__(data).session_path()

    @staticmethod
    def stage_folder(data,stage_name):
        return '{}/{}'.format(SessionPaths.session_folder(data),stage_name)

    @staticmethod
    def tmp_folder(data):
        return '{}/tmp'.format(SessionPaths.session_folder(data))

    @staticmethod
    def stage_outputfile(session_path,stage,fidx_list,fmt='.pkl'):
        folder = '{}/{}/data_'.format(session_path,stage)
        filepath = folder + '_'.join([str(i) for i in fidx_list])
        return filepath+fmt

    @staticmethod
    def session_pkl(data):
        session_path = SessionPaths.session_folder(data)
        return '{}/param_cfg2.pkl'.format(session_path)

    @staticmethod
    def remote_session_folder(data):
        return '~/{}'.format(SessionPaths.__session_args__(data).session_name)

def session_clean(session_args):
    import shutil
    session_folder = SessionPaths.session_folder(session_args)
    shutil.rmtree(session_folder)
    # os.rmdir(session_folder)

def load_session(session_args):
    pkl_file = SessionPaths.session_pkl(session_args)
    if not os.path.isfile(pkl_file):
        session_init(session_args)
    with open(pkl_file,'r') as f:
        return pickle.load(f)

def session_init(sargs):
    session_args = SessionPaths.__session_args__(sargs)
    logger.info('Going to load the config file %s and setup the session', session_args.cfg_filename)
    # loads config file
    sessiondata = SessionData.load_cfg(session_args)
    logger.info('Param config file was successfully loaded')

    # setups up necessary folders
    logger.info('Going to create the session folders')
    setup_local_folders(sessiondata)

    # checks if the hosts are inaccessible, if not create session folder
    setup_remote_folders(sessiondata)

    # stores the pickle file of the session
    fname = SessionPaths.session_pkl(sessiondata)
    logger.info('Going to save configuration of session in a pkl for fast access. This file can be found in {}'.format(fname))
    with open(fname,'wb') as f:
        pickle.dump(sessiondata,f)

    logger.trace('The session path is {}'.format(SessionPaths.session_folder(sessiondata)))

# This function just checks if the hosts are reachable and sets up the session folder
def setup_remote_folders(sessiondata):
    if sessiondata.remote_exists():
        remote_folder = SessionPaths.remote_session_folder(sessiondata)
        logger.info('Going to attempt to reach the hosts and set the session folders')
        for h in sessiondata.hosts():
            out,err = ssh_utils.ssh_run(h,'echo hello world',printstdout=False)
            if out[0] != "hello world\n":
                err_msg = 'I could not ssh to the host {}' % h
                logger.error(err_msg)
                raise AssertionError(err_msg)
            out,err = ssh_utils.ssh_run(h,'mkdir -p '+remote_folder,printstdout=False)
            ssh_utils.ssh_run(h,'mkdir -p '+remote_folder+'/scripts',printstdout=False)

def setup_local_folders(sessiondata):
    def try_mkdir(folder_name):
        logger.info('shell> mkdir -p '+folder_name)
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    session_path = SessionPaths.session_folder(sessiondata)
    stage_names = sessiondata.stage_name_list()

    # sets up the main session folder and tmp folder
    try_mkdir(session_path)
    try_mkdir(SessionPaths.tmp_folder(sessiondata))

    # setup stage folders
    for stage in stage_names:
        stage_task = lf.session_settings.retrieve_task_handler(stage)
        if stage_task.mkdir_flag() is True:
            try_mkdir(SessionPaths.stage_folder(sessiondata,stage))
