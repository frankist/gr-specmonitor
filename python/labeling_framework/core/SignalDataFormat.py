#!/usr/bin/env python
import os
import pickle
import copy
import numpy as np
from ..utils.logging_utils import DynamicLogger
logger = DynamicLogger(__name__)

class StageSignalData:
    def __init__(self,stage_arguments,derived_params,samples = None):
        self.sourcefilename = stage_arguments['sourcefilename']
        self.targetfilename = stage_arguments['targetfilename']
        self.stage_name = stage_arguments['stage_name']
        self.args = stage_arguments['parameters']
        self.derived_params = derived_params
        self.samples = samples # NOTE: should be a list of signals?
        StageSignalData.assert_params_validity(self.args)

    def clear_samples(self):
        if self.samples is not None:
            logger.info('IQ samples of {} were erased'.format(self.targetfilename))
        self.samples = None

    # def is_framed(self):
    #     return True if 'section_bounds' in self.derived_params else False

    @staticmethod
    def assert_params_validity(args):
        assert isinstance(args,dict)

class MultiStageSignalData:
    def __init__(self):
        self.stage_data = {}
        self.prior_stages = []
        self.session_data = {}

    def get_stage_args(self,param_name,stage_name=None):
        if stage_name is None:
            # searches starting from last stage
            for stage in self.prior_stages[::-1]:
                if param_name in self.stage_data[stage].args:
                    return self.stage_data[stage].args[param_name]
        elif stage_name in self.stage_data:
            stage = stage_name
            if param_name in self.stage_data[stage_name].args:
                return self.stage_data[stage_name].args[param_name]
        raise AssertionError('I could not find stage param \'{}\' in \'{}\'. The params were {}'.format(param_name,stage,self.stage_data[stage].args))
        return None # didn't find the argument

    def get_stage_derived_params(self,param_name=None,stage_name=None):
        if stage_name is None:
            # searches starting from last stage
            if param_name is None:
                return self.stage_data[self.prior_stages[-1]].derived_params
            for stage in self.prior_stages[::-1]:
                if param_name in self.stage_data[stage].derived_params:
                    return self.stage_data[stage].derived_params[param_name]
        elif stage_name in self.stage_data:
            if param_name is None:
                return self.stage_data[stage_name].derived_params
            return self.stage_data[stage_name].derived_params[param_name]
        raise AssertionError('I could not find stage param {} in {}'.format(param_name,stage_name))
        return None # didn't find the param

    def get_stage_data(self,stage_name=None):
        stage = stage_name if stage_name is not None else self.prior_stages[-1]
        return self.stage_data[stage]

    def set_stage_data(self,stage_signal_data,clean_flag=True):
        if clean_flag:
            self.clean_previous_samples()
        assert isinstance(stage_signal_data,StageSignalData)
        stage_name = stage_signal_data.stage_name
        if stage_name not in self.prior_stages:
            self.prior_stages.append(stage_name)
            self.stage_data[stage_name] = {}
        self.stage_data[stage_name] = stage_signal_data
        # TODO: assert stage_name is valid

    def clean_previous_samples(self):
        for stage in self.prior_stages:
            self.stage_data[stage].clear_samples()

    def read_stage_samples(self,stage_name=None):#,startidx=0,endidx=None):
        stage = stage_name if stage_name is not None else self.prior_stages[-1]
        assert stage in self.stage_data
        return self.stage_data[stage].samples#read_samples(startidx,endidx)

    def save_pkl(self):
        fname = os.path.expanduser(self.stage_data[self.prior_stages[-1]].targetfilename)
        with open(fname,'w') as f:
            pickle.dump(self,f)

    @classmethod
    def load_pkl(cls,args):
        if isinstance(args,basestring):
            fname = os.path.expanduser(args)
        elif isinstance(args,dict): # it is args
            fname = os.path.expanduser(args['sourcefilename'])
        else:
            raise AssertionError('The args format is not recognized.')
        with open(fname,'r') as f:
            multi_stage_data = pickle.load(f)
        return multi_stage_data

    def join(self,data2):
        assert self.prior_stages==data2.prior_stages
        assert self.session_data==data2.session_data
        for stage_name,sdata in self.stage_data.items():
            if stage_name!=self.prior_stages[-1]: # not the last
                assert sdata==data2.stage_data[stage_name] # confirm they are the same
            else:
                sdata.join(data2.stage_data[stage_name])

def combine_stage_data(stage_data1,stage_data2):
    assert stage_data1.sourcefilename==stage_data2.sourcefilename
    assert stage_data1.targetfilename==stage_data2.targetfilename
    assert stage_data1.stage_name==stage_data2.stage_name
    # assert stage_data1.args==stage_data2.args
    assert len(stage_data1.samples)==len(stage_data2.samples)
    assert isinstance(stage_data1.samples,np.ndarray)

    new_stage_data = copy.deepcopy(stage_data1)
    # combine samples
    new_stage_data.samples += stage_data2.samples

    # combine derived params
    if len(stage_data1.derived_params.keys())!=1 or 'spectrogram_img' not in stage_data1.derived_params:
        raise NotImplementedError('I have to make this more generalizable')
    for k,v in new_stage_data.derived_params.items():
        v2 = stage_data1.derived_params[k].make_superposition(stage_data2.derived_params[k])
        new_stage_data.derived_params[k] = v2

    return new_stage_data

def combine_multi_stage_data(multi_data1,multi_data2):
    assert multi_data1.prior_stages==multi_data2.prior_stages
    assert multi_data1.session_data==multi_data2.session_data
    assert len(multi_data1.stage_data)==len(multi_data2.stage_data)

    new_multi_data = copy.deepcopy(multi_data1)
    for stage_name,sdata in multi_data1.stage_data.items():
        if stage_name!=multi_data1.prior_stages[-1]: # if not last stages
            assert sdata==multi_data2.stage_data[stage_name]
        else:
            new_multi_data.stage_data[stage_name] = combine_stage_data(sdata,multi_data2.stage_data[stage_name])
    return new_multi_data
