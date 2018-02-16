#!/usr/bin/env python

import numpy as np

# labeling_framework package
import specmonitor
from specmonitor import labeling_framework as lf
from specmonitor.labeling_framework.waveform_generators import waveform_generator_utils as wav_utils
logger = lf.DynamicLogger(__name__)

def run(args):
    d = args['parameters']

    x = np.zeros(d['n_samples'])

    # create a StageSignalData structure
    stage_data = wav_utils.set_derived_sigdata(x,args,False)
    metadata = stage_data.derived_params['spectrogram_img']
    tfreq_boxes = metadata.tfreq_boxes
    assert len(tfreq_boxes)==0

    # create a MultiStageSignalData structure and save it
    v = lf.MultiStageSignalData()
    v.set_stage_data(stage_data)
    v.save_pkl()

class NullSourceGenerator(lf.SignalGenerator):
    @staticmethod
    def run(args):
        while True:
            try:
                run(args)
            except RuntimeError, e:
                logger.warning('Failed to generate the null waveform data. Going to rerun. Arguments: {}'.format(args))
                continue
            except KeyError, e:
                logger.error('The input arguments do not seem valid. They were {}'.format(args))
                raise
            break

    @staticmethod
    def name():
        return 'null_source'
