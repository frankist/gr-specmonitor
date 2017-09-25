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

import metadata_handler
import os

# returns the stage number, and the stages run indexes
def parse_filename(f):
    fbase = os.path.splitext(os.path.basename(f))[0]
    pos = fbase.find('data_')
    # TODO: make asserts that we are in the right pos
    tokens = fbase[pos::].split('_')
    return (len(tokens)-1,tokens)

def get_run_all_stages_parameters(handler,filename):
    stage_number,stage_idxs = parse_filename(filename)
    params_per_stage = [list(handler.stage_iterable(s,stage_idxs[s]))[0] for s in range(stage_number)]
    return params_per_stage

def get_run_stage_parameters(handler,filename):
    stage_number,stage_idxs = parse_filename(filename)
    return list(handler.stage_iterable(stage_number,stage_idxs[stage_number]))[0]

def generate_filenames(handler,level_list):
    def generate_stage_filenames(handler,lvl):
        stage_sizes = [handler.get_stage_size(a) for a in range(lvl)]
        return FilenameUtils.get_stage_filename_list(stage_sizes)
    if type(level_list) in [list,tuple]:
        return [generate_stage_filenames(handler,v) for v in level_list]
    return [generate_stage_filenames(handler,level_list)]

class MakeFileSimulator:
    handler_filename = 'handler_params.pkl'

    @staticmethod
    def get_handler():
        return pickle.load(MakeFileSimulator.handler_filename)

    @staticmethod
    def start_sim(cfg_file):
        # NOTE: you should create this metafile in a subfolder to avoid collisions with other running sims
        from cfg_file import stage_params,stage_cmd_parser
        param_handler = metadata_handler.MultiStageParamHandler(stage_params)
        pickle.dump([param_handler,stage_cmd_parser],MakefileSimulator.handler_filename)

    @staticmethod
    def get_filenames(level_list):
        handler,_ = MakeFileSimulator.get_handler()
        fnames = generate_filenames(handler,level_list)
        for f_list in fnames:
            for f in f_list:
                print f

    @staticmethod
    def pickle_cmd_args(filename):
        handler,_ = MakeFileSimulator.get_handler()
        params_of_stage = get_run_stage_parameters(handler,filename)
        pkl_str = pickle.dumps(params_of_stage)
        print pkl_str

    @staticmethod
    def run_cmd(filename):
        handler,cmd_parser = MakeFileSimulator.get_handler()
        stage_number,_ = parse_filename(filename)
        params_of_stage = get_run_stage_parameters(handler,filename)
        cmd_str = cmd_parser(stage_number,params_of_stage)
        pkl_str = pickle.dumps(params_of_stage)
        print cmd_str, pkl_str
