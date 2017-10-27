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

def run_RF_Rx_on_repeat(outputfile,params,sample_rate,Nsuperframe,Nsettle):
    ### Set variables based on given stage parameters
    gaindB = params['rx_gaindB']
    centre_freq = params['rf_frequency']

    # get the needed global parameters
    frame_period = fparams.frame_period
    Rx_num_samples = Nsuperframe+Nsettle # the settle is important both for the HW and pdetec history
    Rx_num_samples += frame_period + 10 # we will only choose peaks whose frame is whole. I just add an guard interval of a few samples

    tb = gr.top_block()
    usrp_source = uhd.usrp_source(
        ",".join(("", "")),
        uhd.stream_args(
        	cpu_format="fc32",
        	channels=range(1),
        ),
    )
    usrp_source.set_samp_rate(sample_rate)
    usrp_source.set_center_freq(centre_freq,0)
    usrp_source.set_gain(gaindB,0)
    head = blocks.head(gr.sizeof_gr_complex,Rx_num_samples)
    fsink = blocks.file_sink(gr.sizeof_gr_complex,outputfile)

    tb.connect(usrp_source,head)
    tb.connect(head,fsink)

    tb.run()

def run_RF_channel(args):
    params = args['parameters']
    sessiondata = args['sessiondata']
    session_folder = SessionParams.SessionPaths.session_folder(sessiondata)
    tmp_folder = SessionParams.SessionPaths.tmp_folder(sessiondata)
    tmp_file = tmp_folder + '/tmp.bin'
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

    # set parameters at remote endpoint. It will lock until the procedure is complete
    d = {'outputfile':tmp_file,'sample_rate':sample_rate,'Nsuperframe':Nsuperframe,'Nsettle':Nsettle,'params':params}
    tmp_params = tmp_folder+'/tmp_params.pkl'
    remote_command = RF_sync_utils.setup_remote_rx(session_folder,tmp_params,targetfilename,"USRPRx",d)

    # call here the Tx or Rx scripts. It will lock until signal is received
    tb = run_RF_Tx_on_repeat(x,params,fparams,sample_rate)
    tb.start()

    # run Rx remotely. It will lock until completion
    ssh_utils.ssh_run("USRPRx","python ~/{}/RF_scripts.py {}".format(session_folder,remote_filename))

    # send signal to stop Tx.
    tb.stop()
    tb.wait()

    # pull results from Rx. It will lock until the SCP is successful
    ssh_utils.scp_recv("USRPRx",tmp_file,tmp_file)

    # save the results
    success = RF_sync_utils.post_process_rx_file_and_save(stage_data,tmp_file,args,fparams,n_sections,Nsuperframe,Nsettle)
    if success is True:
        print 'STATUS: Finished writing to file',targetfilename
    else:
        print 'WARNING: Preamble sync has failed. Going to repeat transmission'
    os.remove(tmp_file)
    # Note: The separation into multiple subsections happens later

if __name__ == '__main__':
    pkl_file = sys.argv[1]
    with open(pkl_file,'r') as f:
        pklparams = pickle.load(f)
    outputfile = pklparams['outputfile']
    params = pklparams['params']
    sample_rate = pklparams['sample_rate']
    Nsuperframe = pklparams['Nsuperframe']
    Nsettle = pklparams['Nsettle']
    run_RF_Rx_on_repeat(outputfile,params,sample_rate,Nsuperframe,Nsettle)