#!/usr/bin/env python

import numpy as np

from ..core.LuigiSimulatorHandler import StageLuigiTask
from ..core import SignalDataFormat as ssa
from ..utils import format_utils as futils
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

def run(args):
    targetfilename = args['targetfilename']

    ### get dependency file, and create a new stage_data object
    multi_stage_data = ssa.MultiStageSignalData.load_pkl(args)
    section = multi_stage_data.read_stage_samples()

    #logger.warning('These are the limits: {}/{}'.format(np.nanmax(section),np.max(section)))

    logger.info('Writing to file {}'.format(targetfilename))
    futils.save_32fc_file(targetfilename,section)

    # section2 = futils.read_32fc_file(targetfilename)
    # print 'section sizes:',section2.size,section.size
    # print 'section max:',np.max(section2),np.max(section)
    # assert np.array_equal(section2,section)

class Convert32fcTask(StageLuigiTask):
    def __init__(self,*args,**kwargs):
        kwargs['output_fmt'] = '.32fc'
        # new_args = args + ('.png',)
        super(Convert32fcTask,self).__init__(*args,**kwargs)

    def run(self):
        this_run_params = self.get_run_parameters()
        run(this_run_params)
