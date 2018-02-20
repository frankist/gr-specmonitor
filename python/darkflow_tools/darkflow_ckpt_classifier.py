import sys
import numpy as np
import cv2

from darkflow.net.build import TFNet
import parse_yolo_cfg as yolocfg

class DarkflowCkptClassifier:
    def __init__(self,yml_config,threshold):
        self.cfg_obj = yolocfg.read_yaml_main_config(yml_config)

        self.options = yolocfg.generate_darkflow_args(self.cfg_obj)
        self.options['threshold'] = threshold
        self.options['load'] = -1 # picks the last one
        self.tfnet = TFNet(self.options)
        assert self.tfnet.FLAGS.threshold>=0

    def classify(self,imgcv):
        if isinstance(imgcv,np.ndarray):
            return self.tfnet.return_predict(imgcv)
        else:
            return self.tfnet.return_predict_batch(imgcv)

    def classify2(self,imgcv,generate_img=True,generate_boxes=True):
        assert isinstance(imgcv, np.ndarray), \
                    'Image is not a np.ndarray'
        h, w, _ = imgcv.shape

        im = self.tfnet.framework.resize_input(imgcv)
        this_inp = np.expand_dims(im, 0)
        feed_dict = {self.tfnet.inp : this_inp}

        out = self.tfnet.sess.run(self.tfnet.out, feed_dict)
        out = out.reshape(out.shape[1],out.shape[2],out.shape[3])#out[1],out[2],out[3])

        newim = None
        if generate_img:
            outcopy = out.copy()
            newim = self.tfnet.framework.postprocess(outcopy,imgcv,save=False,put_text=False)

        boxesInfo = list()
        if generate_boxes:
            boxes = self.tfnet.framework.findboxes(out)
            threshold = self.tfnet.FLAGS.threshold
            for box in boxes:
                tmpBox = self.tfnet.framework.process_box(box, h, w, threshold)
                if tmpBox is None:
                    continue
                boxesInfo.append({
                    "label": tmpBox[4],
                    "confidence": tmpBox[6],
                    "topleft": {
                        "x": tmpBox[0],
                        "y": tmpBox[2]},
                    "bottomright": {
                        "x": tmpBox[1],
                        "y": tmpBox[3]}
                })

        return (newim,boxesInfo)
