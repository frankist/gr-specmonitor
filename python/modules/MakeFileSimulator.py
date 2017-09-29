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
from filename_utils import *

def get_run_all_stages_parameters(handler,filename):
    stage_number,stage_idxs = handler.filename_handler.parse_filename(filename)
    params_per_stage = [list(handler.stage_iterable(s,stage_idxs[s]))[0] for s in range(stage_number)]
    return params_per_stage

def get_run_stage_parameters(handler,filename):
    stage_number,stage_idxs = handler.filename_handler.parse_filename(filename)
    return list(handler.stage_params.stage_iterable(stage_number,stage_idxs[stage_number]))[0]

def generate_filenames(handler,level_list):
    def generate_stage_filenames(handler,lvl):
        stage_sizes = [handler.stage_params.get_stage_size(a) for a in range(lvl+1)]
        return handler.filename_handler.get_stage_filename_list(stage_sizes)
    return [generate_stage_filenames(handler,v) for v in level_list]

# NOTE: you should create this metafile in a subfolder to avoid collisions with other running sims
handler_filename = 'handler_params.pkl'

############## COMMANDS ###############

class SessionCommandParser:
    def __init__(self,session_file,handler_type):
        self.session_file = session_file
        self.handler_type = handler_type

    def __get_handler__(self):
        return self.handler_type.load_handler(self.session_file)

    def parse_config(self,args):
        if os.path.isfile(self.session_file): # If file already exists, do NOTHING
            return
        session_name = args[0]
        cfg_file = args[1]
        session_handler = self.handler_type.load_cfg_file(self.session_file,session_name,cfg_file)
        session_handler.save(self.session_file)

    def get_filenames(self,args):
        if len(args)==0:
            raise ValueError('You must provide a stage name')
        handler = self.__get_handler__()
        stage_nums = [int(handler.stage_name_list().index(args[0]))]
        fnames = generate_filenames(handler,stage_nums)
        for f_list in fnames:
            for f in f_list:
                print f

    def get_dependencies(self,args):
        if len(args)==0:
            raise ValueError('You must provide a filename from where to derive dependencies')
        fname = args[0]
        handler = self.__get_handler__()
        stage_number,stage_idxs = handler.filename_handler.parse_filename(fname)
        print handler.filename_handler.get_stage_filename(stage_idxs[0:-1])

    def apply_transformations(self,args):
        handler = self.__get_handler__()
        print 'gonna apply the transformation for file ',args[0]
        fname = args[0]#handler.filename_handler.get_session_path()+'/'+args[0]
        f = open(fname,'w')
        f.close()

    @classmethod
    def run_cmd(cls,argv,handler_type=mh.SessionParamsHandler):
        session_file = argv[1]
        methodname = argv[2]
        args = argv[3::]
        s = cls(session_file,handler_type)
        method = getattr(s,methodname)
        # possibles = globals().copy()
        # possibles.update(locals())
        # method = possibles.get()
        if not method:
            raise NotImplementedError('Method %s not implemented' % methodname)
        try:
            ret = method(args)
        except ValueError:
            strcmd = ' '.join(argv)
            raise ValueError('ERROR for command: "'+strcmd+'"')
        # except IOError:
        #     strcmd = ' '.join(argv)
        #     raise ValueError('IOERROR for command: "'+strcmd+'"')

############# COMMANDS PARSER #################

# def run_cmd(command_strs):
#     filehandler = command_strs[0]
#     methodname = command_strs[1]
#     args = command_strs[2::]

#     s = SessionCommandParser(filehandler)
#     method = getattr(s, methodname)
#     # possibles = globals().copy()
#     # possibles.update(locals())
#     # method = possibles.get()
#     if not method:
#         raise NotImplementedError('Method %s not implemented' % methodname)
#     method(args)

if __name__ =='__main__':
    run_cmd(sys.argv[1])
