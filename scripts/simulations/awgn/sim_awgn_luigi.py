import sys
sys.path.append('../../../python')
import luigi
import itertools
from labeling_framework.core.LuigiSimulatorHandler import *

class waveform(StageLuigiTask):
    """
    This task generates waveform files
    """
    def requires(self):
        return SessionInit(self.cfg_params)

    def run(self):
        print 'running waveform ',self.stage_idxs
        with self.output().open('w') as out_file:
            print 'creating file'

class Tx(StageLuigiTask):
    def requires(self):
        return waveform(self.cfg_params,self.stage_idxs[0:-1])

    def run(self):
        simdata = LuigiSessionData.load_pkl(self.cfg_params)
        print 'running Tx {}\n'.format(self.stage_idxs)
        with self.output().open('w') as out_file:
            print 'creating file'

class RF(StageLuigiTask):
    def requires(self):
        return Tx(self.cfg_params,self.stage_idxs[0:-1])

    def run(self):
        simdata = LuigiSessionData.load_pkl(self.cfg_params)
        print 'running RF',self.stage_idxs
        with self.output().open('w') as out_file:
            print 'creating file'

class AWGNCmdSession(CmdSession):
    def get_stage_caller(self): # I need to look at the local scope to get the stage_caller
        possibles = globals().copy()
        possibles.update(locals())
        stage_task_caller = possibles.get(self.stage_name)
        return stage_task_caller

if __name__ == "__main__":
    luigi.run()
