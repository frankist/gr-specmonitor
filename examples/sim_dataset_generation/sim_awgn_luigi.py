import sys
sys.path.append('../../python')

import labeling_framework as lf
import labeling_modules
logger = lf.DynamicLogger(__name__)

class Tx(lf.preRFTask):
    @staticmethod
    def depends_on():
        return 'waveform'

class TxImg(lf.ImgSpectrogramBoundingBoxTask):
    @staticmethod
    def depends_on():
        return 'Tx'

class Rx(lf.PartitionSignalTask):
    @staticmethod
    def depends_on():
        return 'Tx'

class RFVOCFormat(lf.VOCFormatTask):
    @staticmethod
    def depends_on():
        return 'Rx'

class TxClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'Tx'
class RxClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'Rx'
class RFVOCFormatClean(lf.RemoveIQSamples):
    @staticmethod
    def depends_on():
        return 'RFVOCFormat'

class AWGNCmdSession(lf.CmdSession):
    pass

if __name__ == "__main__":
    lf.session.run(session=AWGNCmdSession)
