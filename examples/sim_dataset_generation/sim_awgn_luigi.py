import sys
import logging
import luigi

from labeling_framework.core import session_settings
from labeling_framework.waveform_generators.waveform_launcher import *
from labeling_framework.core.LuigiSimulatorHandler import *
from labeling_framework.visualization.visualization_modules import ImgSpectrogramBoundingBoxTask
from labeling_framework.visualization.inspect_labels import Labels2JsonTask
from labeling_framework.data_representation import voc_annotations
from labeling_framework.general_tasks import partition_signal
from labeling_framework.general_tasks import remove_IQsamples
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class Tx(StageLuigiTask):
#    def requires(self):
#        return waveform(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        this_run_params = self.get_run_parameters()
        from labeling_framework.Tx import Tx_transformations
        Tx_transformations.apply_framing_and_offsets(this_run_params)

class TxImg(ImgSpectrogramBoundingBoxTask):#StageLuigiTask):
     pass
#    def requires(self):
#        return Tx(self.session_args,self.stage_idxs[0:-1])

class RFVOCFormat(StageLuigiTask):
#    def requires(self):
#        return Rx(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        this_run_params = self.get_run_parameters()
        voc_annotations.create_image_and_annotation(this_run_params)

class Rx(StageLuigiTask):
#    def requires(self):
#        return Tx(self.session_args,self.stage_idxs[0:-1])

    def run(self):
        this_run_params = self.get_run_parameters()
        partition_signal.run(this_run_params)

# class RxClean(remove_IQsamples.RemoveIQSamples):
#     def stage2clean(self):
#         return 'Rx'

class AWGNCmdSession(CmdSession):
    pass
    #def get_stage_caller(self,stage_name): # I need to look at the local scope to get the stage_caller
    #    return session_settings.retrieve_task_handler(stage_name)
    #    #return possibles.get(stage_name)

def run_before_luigi():
    #possibles = globals().copy()
    #possibles.update(locals())
    session_settings.init()
    session_settings.register_task_handler('waveform',waveform)
    session_settings.register_task_handler('Tx',Tx)
    session_settings.register_task_handler('Rx',Rx)
    session_settings.register_task_handler('TxImg',TxImg)
    session_settings.register_task_handler('RFVOCFormat',RFVOCFormat)
    # session_settings.register_task_handler('RxCleanIQ',remove_IQsamples.IQcleaner_task_factory('Rx'))
    remove_IQsamples.register_IQcleaner_task_handler('Rx')
    remove_IQsamples.register_IQcleaner_task_handler('Tx')
    remove_IQsamples.register_IQcleaner_task_handler('waveform')
    remove_IQsamples.register_IQcleaner_task_handler('RFVOCFormat')
    logging_utils.addLoggingLevel('TRACE',logging.WARNING-5)

if __name__ == "__main__":
    run_before_luigi()
    luigi.run(main_task_cls=AWGNCmdSession, local_scheduler=True)#cmdline_args)
