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

import sys
sys.path.append('../../../python/modules')
sys.path.append('../../../python/labeling_modules')
import MakeFileSimulator

class AWGNSessionCmdParser(MakeFileSimulator.SessionCommandParser):
    def generate_waveform(self,args):
        handler = self.__get_handler__()
        targetfilename = args[0]
        run_parameters = MakeFileSimulator.get_run_stage_parameters(handler,targetfilename)
        d = {'parameters':dict(run_parameters),
             'targetfolder':handler.filename_handler.get_session_path(),
             'targetfilename':targetfilename}
        import waveform_generator
        waveform_generator.waveform_gen_launcher(d)

if __name__ == '__main__':
    # MakeFileSimulator.SessionCommandParser.run_cmd(sys.argv)
    AWGNSessionCmdParser.run_cmd(sys.argv)
