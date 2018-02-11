import sys
sys.path.append('../../python')

from specmonitor import labeling_framework as lf
import labeling_modules
from specmonitor.labeling_framework.RF import RF_scripts
logger = lf.DynamicLogger(__name__)

class Tx(lf.preRFTask):
    @staticmethod
    def depends_on():
        return 'waveform'

class RF(lf.StageLuigiTask):
    @staticmethod
    def depends_on():
        return 'Tx'

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

class TxImg(lf.ImgSpectrogramBoundingBoxTask):
    @staticmethod
    def depends_on():
        return Tx

class RFImg(lf.ImgSpectrogramBoundingBoxTask):
    @staticmethod
    def depends_on():
        return RF

class RFLabels(lf.Labels2JsonTask):
    @staticmethod
    def depends_on():
        return RF

class Rx(lf.PartitionSignalTask):
    @staticmethod
    def depends_on():
        return RF

class RFVOCFormat(lf.VOCFormatTask):
    @staticmethod
    def depends_on():
        return 'Rx'

class waveformClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'waveform'
class TxClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'Tx'
class RFClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'RF'
class RxClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'Rx'
class RFVOCFormatClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'RFVOCFormat'

class OTACmdSession(lf.CmdSession):
    pass

if __name__ == "__main__":
    lf.session.run(session=OTACmdSession)
