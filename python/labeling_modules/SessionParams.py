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
import session_params
import pickle
import ssh_utils

# this class stores all the data necessary to setup a session instance
# - It needs to specify our instance name (e.g. 'sim0')
# - The path to the cfg file where stage params and dependencies are provided
# - The hosts in case we are going to set remote connections
# - It can be loaded from the command line by passing a dictionary
class SessionInstanceArguments:
    def __init__(self,sessionabspath,cfg_file):
        self.sessionabspath = sessionabspath
        self.session_name = os.path.basename(sessionabspath)
        self.cfg_filename = cfg_file
    
    def session_path(self):
        return self.sessionabspath
    
    def session_config_file(self):
        return self.cfg_filename

    @classmethod
    def load_dict(cls,d):
        return cls(d['absolute_path'],d['session_name'],d['cfg_file'])

class SessionData:
    def __init__(self,session_instance_args,stage_params,stage_dependency_tree,ssh_hosts):
        self.session_args = session_instance_args
        self.stage_params = stage_params
        self.stage_dependency_tree = stage_dependency_tree
        self.ssh_hosts = ssh_hosts

    def args(self):
        return self.session_args

    def remote_exists(self):
        return len(self.ssh_hosts)>0

    def stage_name_list(self):
        return self.stage_params.stage_names

    def hosts(self):
        return self.ssh_hosts
    
    @classmethod
    def load_cfg(cls,session_args):
        cfg_file = session_args.session_config_file()
        # Remove the extension and load the cfg_file
        fbase = os.path.splitext(os.path.basename(cfg_file))[0]
        try:
            cfg_module = importlib.import_module(fbase) # TODO: Find an appropriate format that is not a python file load
        except Exception, e:
            print 'Error while opening config file: ',str(e)
            exit(-1)
        # TODO: Parse the module to see if every variable is initialized
        sp = session_params.TaggedMultiStageParams(cfg_module.tags,
                                                   cfg_module.stage_names,
                                                   cfg_module.stage_params)
        dep_tree = cfg_module.stage_dependency_tree if hasattr(cfg_module,'stage_dependency_tree') else None
        hosts = cfg_module.ssh_hosts if hasattr(cfg_module,'ssh_hosts') else None
        return cls(session_args,sp,dep_tree,hosts)

# This class is only an interface to generate appropriate folder paths, and filename formats
# This way i separate the concerns of each class and I have one single point where I make changes to the file/folder names
class SessionPaths:
    @staticmethod
    def __session_args__(data): # receives or either sessioninstancearguments or sessiondata
        return data if isinstance(data,SessionInstanceArguments) else data.args()

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
    def stage_outputfile(session,stage,fidx_list):
        folder = '{}/{}/data_'.format(session,stage)
        filepath = folder + '_'.join([str(i) for i in fidx_list])
        return filepath+'.pkl'

    @staticmethod
    def session_pkl(data):
        session_path = SessionPaths.session_folder(data)
        return '{}/param_cfg2.pkl'.format(session_path)

def session_clean(session_args):
    session_folder = SessionPaths.session_folder(session_args)
    os.rmdir(session_folder)

def try_session_init(session_args):
    pkl_file = SessionPaths.session_pkl(session_args)
    if not os.path.exists(pkl_file):
        session_init(session_args)

def session_init(session_args):
    print 'STATUS: Going to load the config file and setup the session'
    # loads config file
    sessiondata = SessionData.load_cfg(session_args)
    print 'STATUS: Config file was successfully loaded'

    # setups up necessary folders
    print 'STATUS: Going to create the session folders'
    setup_local_folders(sessiondata)

    # checks if the hosts are inaccessible
    if sessiondata.remote_exists():
        print 'STATUS: Going to try to reach the hosts'
        for h in sessiondata.hosts():
            out,err = ssh_utils.ssh_run(h,'echo hello world',printstdout=False)
            if out[0] != "hello world\n":
                print 'ERROR: Could not ssh to the host',h
                exit(-1)

    # stores the pickle file of the session
    print 'STATUS: Going to save configuration of session for fast access'
    with open(SessionPaths.session_pkl(sessiondata),'wb') as f:
        pickle.dump(sessiondata,f)

def setup_local_folders(sessiondata):
    def try_mkdir(folder_name):
        print '> mkdir',folder_name
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    session_path = SessionPaths.session_folder(sessiondata)
    stage_names = sessiondata.stage_name_list()

    # sets up the main session folder and tmp folder
    try_mkdir(session_path)
    try_mkdir(SessionPaths.tmp_folder(sessiondata))

    # setup stage folders
    for stage in stage_names:
        try_mkdir(SessionPaths.stage_folder(sessiondata,stage))