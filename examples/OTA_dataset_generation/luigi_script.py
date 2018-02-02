import sys

from labeling_framework import session
from labeling_framework.waveform_generators.waveform_launcher import *
from labeling_framework.core.LuigiSimulatorHandler import StageLuigiTask
from labeling_framework.visualization.visualization_modules import ImgSpectrogramBoundingBoxTask
from labeling_framework.visualization.inspect_labels import Labels2JsonTask
from labeling_framework.RF import RF_scripts
from labeling_framework.data_representation import voc_annotations
from labeling_framework.general_tasks import partition_signal
from labeling_framework.general_tasks import remove_IQsamples
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

class Tx(StageLuigiTask):
    @staticmethod
    def depends_on():
        return waveform
    def run(self):
        this_run_params = self.get_run_parameters()
        from labeling_framework.Tx import Tx_transformations
        Tx_transformations.apply_framing_and_offsets(this_run_params)

class RF(StageLuigiTask):
    @staticmethod
    def depends_on():
        return Tx

    def requires(self):
        return [RF_scripts.RemoteSetup(self.session_args),Tx(self.session_args,self.stage_idxs[0:-1])]

    def run(self):
        this_run_params = self.get_run_parameters()
        success = False
        counter = 0
        while success is False:
            success = RF_scripts.run_RF_channel(this_run_params)
            counter += 1
            logger.trace('This is the try no. {}'.format(counter))

class TxImg(ImgSpectrogramBoundingBoxTask):#StageLuigiTask):
    @staticmethod
    def depends_on():
        return Tx

    def requires(self):
        return Tx(self.session_args,self.stage_idxs[0:-1])

class RFImg(ImgSpectrogramBoundingBoxTask):
    @staticmethod
    def depends_on():
        return RF

class RFLabels(Labels2JsonTask):
    @staticmethod
    def depends_on():
        return RF

class Rx(StageLuigiTask):
    @staticmethod
    def depends_on():
        return RF

    def run(self):
        this_run_params = self.get_run_parameters()
        partition_signal.run(this_run_params)

class RFVOCFormat(StageLuigiTask):
    @staticmethod
    def depends_on():
        return Rx

    def run(self):
        this_run_params = self.get_run_parameters()
        voc_annotations.create_image_and_annotation(this_run_params)

class waveformClean(remove_IQsamples.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'waveform'
class TxClean(remove_IQsamples.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return Tx
class RFClean(remove_IQsamples.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return RF
class RxClean(remove_IQsamples.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return Rx
class RFVOCFormatClean(remove_IQsamples.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return RFVOCFormat

class OTACmdSession(CmdSession):
    pass

if __name__ == "__main__":
    session.run(session=OTACmdSession)
