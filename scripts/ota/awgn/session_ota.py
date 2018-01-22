import sys
# sys.path.append('../../../python')
import logging
import luigi

from labeling_framework.core import session_settings
from labeling_framework.waveform_generators.waveform_launcher import *
from labeling_framework.core.LuigiSimulatorHandler import *
from labeling_framework.visualization.visualization_modules import ImgSpectrogramBoundingBoxTask
from labeling_framework.visualization.inspect_labels import Labels2JsonTask
from labeling_framework.RF import RF_scripts
from labeling_framework.data_representation import voc_annotations
from labeling_framework.general_tasks import partition_signal
from labeling_framework.general_tasks import remove_IQsamples
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class Tx(StageLuigiTask):
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

    def run(self):
        this_run_params = self.get_run_parameters()
        is_signal_insync = True
        mark_box = True
        import visualization_modules
        visualization_modules.generate_spectrogram_imgs(this_run_params,is_signal_insync, mark_box)

class RFImg(ImgSpectrogramBoundingBoxTask):
    pass

class RFLabels(Labels2JsonTask):
    pass

class RFVOCFormat(StageLuigiTask):
    def run(self):
        this_run_params = self.get_run_parameters()
        voc_annotations.create_image_and_annotation(this_run_params)

class Rx(StageLuigiTask):
    def run(self):
        this_run_params = self.get_run_parameters()
        partition_signal.run(this_run_params)

class AWGNCmdSession(CmdSession): # consider deleting
    pass

def run_before_luigi():
    #     # possibles = globals().copy()
    #     # possibles.update(locals())
    #     # return possibles.get(stage_name)
    session_settings.init()
    session_settings.register_task_handler('waveform',waveform)
    session_settings.register_task_handler('Tx',Tx)
    session_settings.register_task_handler('RF',RF)
    session_settings.register_task_handler('Rx',Rx)
    session_settings.register_task_handler('TxImg',TxImg)
    session_settings.register_task_handler('RFImg',RFImg)
    session_settings.register_task_handler('RFVOCFormat',RFVOCFormat)
    session_settings.register_task_handler('RFLabels',RFLabels)
    remove_IQsamples.register_IQcleaner_task_handler('waveform')
    remove_IQsamples.register_IQcleaner_task_handler('Tx')
    remove_IQsamples.register_IQcleaner_task_handler('RF')
    remove_IQsamples.register_IQcleaner_task_handler('Rx')
    remove_IQsamples.register_IQcleaner_task_handler('RFVOCFormat')

    logging_utils.addLoggingLevel('TRACE',logging.WARNING-5)


if __name__ == "__main__":
    run_before_luigi()
    luigi.run(main_task_cls=AWGNCmdSession, local_scheduler=True)
