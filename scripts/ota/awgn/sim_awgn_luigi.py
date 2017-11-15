
import sys
sys.path.append('../../../python')
# sys.path.append('../../../python/modules')
# sys.path.append('../../../python/labeling_modules')
# sys.path.append('../../../python/labeling_scripts')
# sys.path.append('../../../python/utils')
# sys.path.append('../../../python/labeling_scripts')
# sys.path.append('../../../python/labeling_framework')
# sys.path.append('../../../python/labeling_framework/waveform_generators')
from labeling_framework.waveform_generators.waveform_launcher import *
import luigi
from labeling_framework.core.LuigiSimulatorHandler import *
from labeling_framework.visualization.visualization_modules import ImgSpectrogramBoundingBoxTask
from labeling_framework.RF import RF_scripts
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class Tx(StageLuigiTask):
    def requires(self):
        return waveform(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        this_run_params = self.get_run_parameters()
        from labeling_framework.Tx import Tx_transformations
        Tx_transformations.apply_framing_and_offsets(this_run_params)


class RF(StageLuigiTask):
    def requires(self):
        return [RF_scripts.RemoteSetup(self.session_args),Tx(self.session_args,self.stage_idxs[0:-1])]

    def run(self):
        this_run_params = self.get_run_parameters()
        RF_scripts.run_RF_channel(this_run_params)

class TxImg(StageLuigiTask):
    def __init__(self,*args,**kwargs):
        kwargs['output_fmt'] = '.png'
        # new_args = args + ('.png',)
        super(TxImg,self).__init__(*args,**kwargs)

    def requires(self):
        return Tx(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        this_run_params = self.get_run_parameters()
        is_signal_insync = True
        mark_box = True
        import visualization_modules
        visualization_modules.generate_spectrogram_imgs(this_run_params,is_signal_insync, mark_box)

class RFImg(ImgSpectrogramBoundingBoxTask):
    def requires(self):
        return RF(self.session_args,self.stage_idxs[0:-1])

class AWGNCmdSession(CmdSession):
    def get_stage_caller(self,stage_name): # I need to look at the local scope to get the stage_caller
        possibles = globals().copy()
        possibles.update(locals())
        return possibles.get(stage_name)

def run_before_luigi():
    import logging
    logging_utils.addLoggingLevel('TRACE',logging.WARNING-5)
    # print 'LASLDDLASLDLASDL args:',sys.argv

run_before_luigi()

if __name__ == "__main__":
    luigi.run()
