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
sys.path.append('../../../python/labeling_scripts')
sys.path.append('../../../python/utils')
import MakeFileSimulator
import SessionParams
import importlib

class AWGNSessionCmdParser(MakeFileSimulator.SessionCommandParser):
    def generate_waveform(self,args):
        handler = self.__get_handler__()
        targetfilename = args[0]
        run_parameters = MakeFileSimulator.get_run_stage_parameters(handler,targetfilename)
        d = {'parameters':dict(run_parameters),
             'targetfolder':handler.filename_handler.get_session_path(),
             'targetfilename':targetfilename,
             'stage_name':'waveform'}
        import waveform_generator
        waveform_generator.waveform_gen_launcher(d)
    
    def apply_tx_transformations(self,args):
        handler = self.__get_handler__()
        targetfilename = args[0]
        sourcefilename = self.__get_dependency_file__(targetfilename)
        run_parameters = MakeFileSimulator.get_run_stage_parameters(handler,targetfilename)
        d = {'parameters':dict(run_parameters),'targetfolder':handler.filename_handler.get_session_path(),
             'targetfilename':targetfilename,'sourcefilename':sourcefilename,
             'stage_name':'Tx','previous_stage_name':'waveform'}
        import Tx_transformations
        Tx_transformations.apply_framing_and_offsets(d)
        print 'done.'

    def run_RF_channel(self,args):
        handler = self.__get_handler__()
        targetfilename = args[0]
        sourcefilename = self.__get_dependency_file__(targetfilename)
        run_parameters = MakeFileSimulator.get_run_stage_parameters(handler,targetfilename)
        d = {'parameters':dict(run_parameters),'sessiondata':self.sessiondata,#handler.filename_handler.get_session_path(),
             'targetfilename':targetfilename,'sourcefilename':sourcefilename,
             'stage_name':'RF','previous_stage_name':'Tx'}
        import RF_scripts
        RF_scripts.run_RF_channel(d)
    
    def transfer_files_to_remote(self,args):
        handler = self.__get_handler__()
        if self.sessiondata.remote_exists():
            def find_script_path(script_name): # TODO: make this better
                modu = importlib.import_module(script_name)
                base = os.path.splitext(os.path.basename(modu.__file__))[0] # take the pyc out
                absp = os.path.splitext(os.path.abspath(modu.__file__))[0] # take the pyc out
                return (base,absp+'.py')
            remote_folder = SessionParams.SessionPaths.remote_session_folder(self.sessiondata)
            # find path of files to transfer
            #import inspect
            import os
            import ssh_utils
            scripts = ['remote_RF_script']
            script_paths = [find_script_path(s) for s in scripts]
            # for f in folder_names:
            #     folders[f] = os.path.dirname(inspect.getfile(f))
                # labeling_scripts_folder = [s for s in sys.path if os.path.basename(s)=='labeling_scripts']
            for h in self.sessiondata.hosts():
                for tup in script_paths:
                    remote_path = remote_folder+'/scripts/'+tup[0]+'.py'
                    print 'Going to transfer script {} to remote {}'.format(tup[1],h)
                    ssh_utils.scp_send(h,tup[1],remote_path)

if __name__ == '__main__':
    # MakeFileSimulator.SessionCommandParser.run_cmd(sys.argv)
    AWGNSessionCmdParser.run_cmd(sys.argv)
