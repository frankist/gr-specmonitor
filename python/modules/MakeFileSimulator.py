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

import metadata_handler as mh
import os
import pickle
import importlib

# returns the stage number, and the stages run indexes
def parse_filename(f):
    fbase = os.path.splitext(os.path.basename(f))[0]
    pos = fbase.find('data_')
    # TODO: make asserts that we are in the right pos
    tokens = fbase[pos::].split('_')
    return (len(tokens)-2,[int(i) for i in tokens[1::]])

def get_run_all_stages_parameters(handler,filename):
    stage_number,stage_idxs = parse_filename(filename)
    params_per_stage = [list(handler.stage_iterable(s,stage_idxs[s]))[0] for s in range(stage_number)]
    return params_per_stage

def get_run_stage_parameters(handler,filename):
    stage_number,stage_idxs = parse_filename(filename)
    return list(handler.stage_iterable(stage_number,stage_idxs[stage_number]))[0]

def generate_filenames(handler,level_list):
    def generate_stage_filenames(handler,lvl):
        stage_sizes = [handler.stage_params.get_stage_size(a) for a in range(lvl+1)]
        return mh.FilenameUtils.get_stage_filename_list(handler.stage_names,stage_sizes)
    return [generate_stage_filenames(handler,v) for v in level_list]

# NOTE: you should create this metafile in a subfolder to avoid collisions with other running sims
handler_filename = 'handler_params.pkl'

############## COMMANDS ###############

class SessionCommandParser:
    def __init__(self,session_name,handler_type):
        self.session_name = session_name
        self.handler_type = handler_type

    def __get_handler__(self):
        return self.handler_type.load_handler(self.session_name)

    def start_session(self,args):
        cfg_file = args[0]
        session_handler = self.handler_type.load_cfg_file(self.session_name,cfg_file)
        session_handler.save()
        # fbase = os.path.splitext(os.path.basename(cfg_file))[0]
        # cfg_module = importlib.import_module(fbase)
        # session_handler = SimParamsHandler(cfg_module)
        # param_handler = mh.MultiStageParamHandler(cfg_module.test_params)
        # with open(hfname,'wb') as f:
        #     pickle.dump(param_handler, f)

    def get_filenames(self,args):
        stage_nums = [int(args[0])]
        handler = self.__get_handler__()
        fnames = generate_filenames(handler,stage_nums)
        for f_list in fnames:
            for f in f_list:
                print f

    @staticmethod
    def pickle_cmd_args(filename):
        handler = get_handler()
        params_of_stage = get_run_stage_parameters(handler,filename)
        pkl_str = pickle.dumps(params_of_stage)
        print pkl_str

    @classmethod
    def run_cmd(cls,argv,handler_type=mh.SimParamsHandler):
        session_name = argv[1]
        methodname = argv[2]
        args = argv[3::]
        s = cls(session_name,handler_type)
        method = getattr(s,methodname)
        # possibles = globals().copy()
        # possibles.update(locals())
        # method = possibles.get()
        if not method:
            raise NotImplementedError('Method %s not implemented' % methodname)
        method(args)



############# COMMANDS PARSER #################

def run_cmd(command_strs):
    filehandler = command_strs[0]
    methodname = command_strs[1]
    args = command_strs[2::]

    s = SessionCommandParser(filehandler)
    method = getattr(s, methodname)
    # possibles = globals().copy()
    # possibles.update(locals())
    # method = possibles.get()
    if not method:
        raise NotImplementedError('Method %s not implemented' % methodname)
    method(args)

if __name__ =='__main__':
    run_cmd(sys.argv[1])
