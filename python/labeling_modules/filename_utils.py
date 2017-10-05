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
import itertools

class SessionFilenamesHandler:
    def __init__(self,session_file,session_name,stage_names):
        self.session_file = session_file
        self.session_name = session_name
        self.stage_name_list = stage_names

    def get_session_path(self):
        return os.path.dirname(self.session_file)

    def get_stage_format(self,stage_number):
        fmt_str = '{0}/{1}/data'.format(self.get_session_path(),self.stage_name_list[stage_number])
        fmt_str += '_{}'*(stage_number+1)
        fmt_str += '.pkl'
        return fmt_str

    def get_stage_filename(self,stage_run_idxs):
        stage_number = len(stage_run_idxs)-1
        fmt_str = self.get_stage_format(stage_number)
        return fmt_str.format(*stage_run_idxs)

    def get_stage_filename_list(self,stage_sizes):
        stage_number = len(stage_sizes)-1
        fmt_str = self.get_stage_format(stage_number)
        prod_file_idxs = itertools.product(*[range(a) for a in stage_sizes])
        return [fmt_str.format(*v) for v in prod_file_idxs]

    # returns the stage number, and the stages run indexes
    def parse_filename(self,f):
        fbase = os.path.splitext(os.path.basename(f))[0]
        pos = fbase.find('data_')
        # TODO: make asserts that we are in the right pos
        tokens = fbase[pos::].split('_')
        return (len(tokens)-2,[int(i) for i in tokens[1::]])

    def get_stage_name(self,stage_number):
        return self.stage_name_list[stage_number]

    def get_file_stage_name(self,filename):
        stage_number,_ = self.parse_filename(filename)
        return self.get_stage_name(stage_number)

    def get_dependency_filename(self,filename):
        stage_number,stage_idxs = self.parse_filename(filename)
        return self.get_stage_filename(stage_idxs[0:-1])
    
if __name__ == '__main__':
    pass
