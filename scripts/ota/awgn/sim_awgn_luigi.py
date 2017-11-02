import sys
sys.path.append('../../../python/modules')
sys.path.append('../../../python/labeling_modules')
sys.path.append('../../../python/labeling_scripts')
sys.path.append('../../../python/utils')
import luigi
import itertools
from LuigiSimulatorHandler import *
import logging
import waveform_generator

class waveform(StageLuigiTask):
    """
    This task generates waveform files
    """
    def requires(self):
        return SessionInit(self.session_args)

    def run(self):
        logging.debug('Running Waveform Generator')
        this_run_params = self.get_run_parameters()
        waveform_generator.waveform_gen_launcher(this_run_params)
    
class Tx(StageLuigiTask):
    def requires(self):
        return waveform(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        sessiondata = self.load_sessiondata()
        print 'running Tx {}\n'.format(self.stage_idxs)
        with self.output().open('w') as out_file:
            print 'creating file'

class RF(StageLuigiTask):
    def requires(self):
        return Tx(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        sessiondata = self.load_sessiondata()
        print 'running RF',self.stage_idxs
        with self.output().open('w') as out_file:
            print 'creating file'

class AWGNCmdSession(CmdSession):
    def get_stage_caller(self,stage_name): # I need to look at the local scope to get the stage_caller
        possibles = globals().copy()
        possibles.update(locals())
        return possibles.get(stage_name)

if __name__ == "__main__":
    luigi.run()