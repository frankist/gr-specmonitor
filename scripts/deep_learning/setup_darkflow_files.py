import sys
sys.path.append('../../scripts/deep_learning')

import parse_yolo_cfg as yolocfg
import voc_tools
import darknet_scripts

def setup_darkflow_files(cfg_filename):
    cfg_obj = yolocfg.read_yaml_main_config(cfg_filename)
    cfg_model = cfg_obj.model_params()

    # setup labels file
    labels_file = cfg_obj.labels_filename()
    classes_list = cfg_model['classes']
    voc_tools.write_labels_file(labels_file,classes_list)

    # this basically computes the optimal anchors for the dataset
    if cfg_model['find_anchors']==True:
        voc_tools.setup_darknet_dataset(cfg_obj)
        darknet_scripts.write_anchors_from_params_dict(cfg_obj)
