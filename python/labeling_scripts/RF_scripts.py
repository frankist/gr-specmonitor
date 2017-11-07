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

from gnuradio import gr
from gnuradio import blocks
from gnuradio import channels
import sys
import os
import time
from bounding_box import *
import pkl_sig_format
import preamble_utils
import filedata_handling as filedata
import pickle
import RF_sync_utils
from gnuradio import uhd
import ssh_utils
import SessionParams
from LuigiSimulatorHandler import SessionLuigiTask
import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def setup_RF_Tx_on_repeat(framed_signal,params,fparams,sample_rate):
    ### Set variables based on given parameters
    gaindB = params['tx_gaindB']
    centre_freq = params['rf_frequency']

    # read samples already framed, apply USRP params, and keep transmitting until interruption
    tb = gr.top_block()
    vector_source = blocks.vector_source_c(framed_signal,True) # keep repeating
    usrp_sink = uhd.usrp_sink(
        ",".join(("", "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    usrp_sink.set_samp_rate(sample_rate)
    usrp_sink.set_center_freq(centre_freq,0)
    usrp_sink.set_gain(gaindB,0)

    tb.connect(vector_source,(usrp_sink,0))
    
    return tb

def run_RF_channel(args):
    params = args['parameters']
    sessiondata = args['sessiondata']
    session_folder = SessionParams.SessionPaths.session_folder(sessiondata)
    tmp_folder = SessionParams.SessionPaths.tmp_folder(sessiondata)
    tmp_file = tmp_folder+'/tmp.bin'
    targetfilename = args['targetfilename']
    sourcefilename = args['sourcefilename']
    stage_name = args['stage_name']

    ### Read previous stage data and sets the parameters of the new stage
    freader = pkl_sig_format.WaveformPklReader(sourcefilename)
    stage_data = freader.data()
    filedata.set_stage_parameters(stage_data,stage_name,params)
    x = np.array(freader.read_section(),np.complex128)

    # get parameters from other stages
    fparams = filedata.get_frame_params(stage_data)
    n_sections = filedata.get_stage_parameter(stage_data,'num_sections')
    Nsuperframe = filedata.get_num_samples_with_framing(stage_data) # it is basically frame_period*num_frames
    assert x.size>=Nsuperframe
    sample_rate = filedata.get_stage_parameter(stage_data,'sample_rate')
    Nsettle = int(params['settle_time'] * sample_rate)
    n_skip_samples,n_rx_samples,_ = RF_sync_utils.get_recording_params(Nsettle,Nsuperframe,fparams.frame_period)

    # set parameters at remote endpoint. It will lock until the procedure is complete
    d = {'sample_rate':sample_rate,'n_rx_samples':n_rx_samples,'n_skip_samples':n_skip_samples,'params':params}
    remote_cmd,remote_tmp_file,clear_cmd = RF_sync_utils.setup_remote_rx(sessiondata,"USRPRx",d)

    # call here the Tx or Rx scripts. It will lock until signal is received
    tb = setup_RF_Tx_on_repeat(x,params,fparams,sample_rate)
    print 'Going to start Tx flowgraph'
    tb.start()

    # run Rx remotely. It will lock until completion
    ssh_utils.ssh_run("USRPRx",remote_cmd,logfilename=tmp_folder+'/ssh_USRPRx_log.txt')

    # send signal to stop Tx.
    tb.stop()
    tb.wait()
    print 'Tx flowgraph finished successfully'

    # pull results from Rx. It will lock until the SCP is successful
    ssh_utils.scp_recv("USRPRx",tmp_file,remote_tmp_file)
    print 'this is the resulting file size:',os.path.getsize(tmp_file)
    ssh_utils.ssh_run("USRPRx",clear_cmd)

    # save the results
    success = RF_sync_utils.post_process_rx_file_and_save(stage_data,tmp_file,args,fparams,n_sections,Nsuperframe,Nsettle)
    if success is True:
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later

class RemoteSetup(SessionLuigiTask):
    def run(self):
        sessiondata = self.load_sessiondata()
        scp_out = {}

        if sessiondata.remote_exists():
            remote_folder = SessionParams.SessionPaths.remote_session_folder(sessiondata)
            scripts = ['remote_RF_script']

            def find_script_path(script_name): # TODO: make this better
                import importlib
                modu = importlib.import_module(script_name)
                base = os.path.splitext(os.path.basename(modu.__file__))[0] # take the pyc out
                absp = os.path.splitext(os.path.abspath(modu.__file__))[0] # take the pyc out
                return (base,absp+'.py')

            # find path of files to transfer
            script_paths = [find_script_path(s) for s in scripts]
            for h in sessiondata.hosts():
                for tup in script_paths:
                    remote_path = remote_folder+'/scripts/'+tup[0]+'.py'
                    logger.info('Going to transfer script {} to remote {}'.format(tup[1],h))
                    r,e = ssh_utils.scp_send(h,tup[1],remote_path)
                    scp_out[h] = {'cout':r,'err':e}

        with open(self.output().path,'w') as f:
            pickle.dump(scp_out,f)

            # def find_script_path(script_name): # TODO: make this better
            #     modu = importlib.import_module(script_name)
            #     base = os.path.splitext(os.path.basename(modu.__file__))[0] # take the pyc out
            #     absp = os.path.splitext(os.path.abspath(modu.__file__))[0] # take the pyc out
            #     return (base,absp+'.py')
            # remote_folder = SessionParams.SessionPaths.remote_session_folder(self.sessiondata)
            # # find path of files to transfer
            # #import inspect
            # import os
            # import ssh_utils
            # scripts = ['remote_RF_script']
            # script_paths = [find_script_path(s) for s in scripts]
            # for h in self.sessiondata.hosts():
            #     for tup in script_paths:
            #         remote_path = remote_folder+'/scripts/'+tup[0]+'.py'
            #         print 'Going to transfer script {} to remote {}'.format(tup[1],h)
            #         ssh_utils.scp_send(h,tup[1],remote_path)