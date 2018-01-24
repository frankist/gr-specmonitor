import sys
import numpy as np
import cv2

import parse_yolo_cfg as yolocfg

class DarkflowCkptClassifier:
    def __init__(self,yml_config):
        self.cfg_obj = yolocfg.read_yaml_main_config(yml_config)

        # darkflow is loaded dynamically for now
        darkflow_folder = self.cfg_obj.darkflow_bin_path()
        sys.path.append(darkflow_folder)
        from darkflow.net.build import TFNet

        self.options = yolocfg.generate_darkflow_args(self.cfg_obj)
        # self.options = run_darkflow.darkflow_parse_config(self.cfg_obj)
        self.options['load'] = -1 # picks the last one
        self.tfnet = TFNet(self.options)

    def classify(self,imgcv):
        result = self.tfnet.return_predict(imgcv)
        return result
