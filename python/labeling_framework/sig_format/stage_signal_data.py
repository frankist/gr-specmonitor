#!/usr/bin/env python
import os
import pickle

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
