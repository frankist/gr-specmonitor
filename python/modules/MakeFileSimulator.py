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
import time
import SessionParams
import visualization_modules

def get_run_all_stages_parameters(handler,filename):
    stage_number,stage_idxs = handler.filename_handler.parse_filename(filename)
    params_per_stage = [list(handler.get_stage_iterable(s,stage_idxs[s]))[0] for s in range(stage_number)]
    return params_per_stage

def get_run_stage_parameters(handler,filename):
    stage_number,stage_idxs = handler.filename_handler.parse_filename(filename)
    return list(handler.stage_params.get_stage_iterable(stage_number,stage_idxs[stage_number]))[0]

def generate_filenames(handler,level_list):
    def generate_stage_filenames(handler,lvl):
        stage_sizes = [handler.stage_params.length(stage=a) for a in range(lvl+1)]
        return handler.filename_handler.get_stage_filename_list(stage_sizes)
    return [generate_stage_filenames(handler,v) for v in level_list]

############## COMMANDS ###############

class SessionCommandParser:
    def __init__(self,session_file,cfg_file,handler_type):
        self.session_file = session_file#os.path.abspath(session_file)
        dirname = os.path.dirname(self.session_file)
        self.session_name = os.path.split(dirname)[1]
        self.cfg_filename = cfg_file
        self.handler_type = handler_type
        self.handler = None

    def __get_handler__(self):
        if self.handler is None:
            if os.path.isfile(self.session_file):
                self.handler = self.handler_type.load_handler(self.session_file)
            else:
                self.handler = self.setup_new_session()
        return self.handler

    def __get_dependency_file__(self,this_file):
        handler = self.__get_handler__()
        return handler.filename_handler.get_dependency_filename(this_file)
        # stage_number,stage_idxs = handler.filename_handler.parse_filename(this_file)
        # return handler.filename_handler.get_stage_filename(stage_idxs[0:-1])

    def setup_new_session(self):
        if not os.path.isfile(self.cfg_filename):
            raise IOError('Config file does not exist')
        session_handler = self.handler_type.load_cfg_file(self.session_file,self.session_name,self.cfg_filename)
        session_handler.save(self.session_file)
        return session_handler

    def check_handler(self,args):
        handler = self.__get_handler__()

    def load_session(self,args):
        sessionabspath = os.path.dirname(os.path.abspath(self.session_file))
        session_args = SessionParams.SessionInstanceArguments(sessionabspath,self.cfg_filename)
        SessionParams.try_session_init(session_args)

    def get_filenames(self,args):
        if len(args)==0:
            print 'You must provide a stage name'
            exit(-1)
        handler = self.__get_handler__()
        stage_nums = [int(handler.stage_name_list().index(args[0]))]
        fnames = generate_filenames(handler,stage_nums)
        for f_list in fnames:
            for f in f_list:
                print f

    def get_dependencies(self,args):
        if len(args)==0:
            print 'You must provide a filename from where to derive dependencies'
            exit(-1)
        fname = args[0]
        print self.__get_dependency_file__(fname)

    def get_spectrogram_img(self,args):
        # FIXME: Make this more elegant
        sourcefilename = args[0]
        is_signal_insync = args[1]=='True'
        mark_box = args[1]=='True'
        visualization_modules.save_spectrograms(sourcefilename,is_signal_insync, mark_box)

    @classmethod
    def run_cmd(cls,argv,handler_type=mh.SessionParamsHandler):
        session_file = argv[1]
        cfg_file = argv[2]
        methodname = argv[3]
        args = argv[4::]
        s = cls(session_file,cfg_file,handler_type)
        method = getattr(s,methodname)
        # possibles = globals().copy()
        # possibles.update(locals())
        # method = possibles.get()
        if not method:
            raise NotImplementedError('Method %s not implemented' % methodname)
        # try:
        ret = method(args)
        # except ValueError:
        #     strcmd = ' '.join(argv)
        #     raise ValueError('ERROR for command: "'+strcmd+'"')
        # except IOError:
        #     strcmd = ' '.join(argv)
        #     raise ValueError('IOERROR for command: "'+strcmd+'"')

############# COMMANDS PARSER #################

if __name__ =='__main__':
    run_cmd(sys.argv[1])
