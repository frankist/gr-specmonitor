#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

from ..core import SignalDataFormat as ssa
from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

def generate_psd(this_run_params):
    # load data from previous stage
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(this_run_params)
    x = multi_stage_data.read_stage_samples()
    spec_metadata = multi_stage_data.get_stage_derived_params('spectrogram_img')
    num_sections = len(spec_metadata)
    assert num_sections==1 # TODO: Implement this for several subsections

    # load other parameters
    targetfile = this_run_params['targetfilename']
    # sourcefile = this_run_params['sourcefilename']

    # plot
    PSD = np.abs(np.fft.fftshift(np.fft.fft(x)))**2
    PSDdB = 10*np.log10(PSD)

    # save figure
    fig, ax = plt.subplots( nrows=1, ncols=1 )  # create figure & 1 axis
    ax.plot(PSDdB)
    fig.savefig(targetfile)   # save the figure to file
    plt.close(fig)    # close the figure

class PSDPlotTask(StageLuigiTask):
    def __init__(self,*args,**kwargs):
        kwargs['output_fmt'] = '.png'
        super(PSDPlotTask,self).__init__(*args,**kwargs)

    def run(self):
        this_run_params = self.get_run_parameters()
        generate_psd(this_run_params)
