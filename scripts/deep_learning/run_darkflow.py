import sys
sys.path.append('../../python/darkflow_tools')
import argparse
import os
import subprocess
import cv2

import parse_yolo_cfg as yolocfg
import voc_tools
import darknet_scripts

def setup_darkflow_files(cfg_obj):
    """
    Setup the basic files for running darkflow. These include:
    -   labels txt file
    if find_anchors is True:
    -   generate anchors fitted to the given dataset
    """
    cfg_model = cfg_obj.model_params()

    # setup labels file
    labels_file = cfg_obj.labels_filename()
    classes_list = cfg_model['classes']
    voc_tools.write_labels_file(labels_file,classes_list)

    # this basically computes the optimal anchors for the dataset
    if cfg_model['find_anchors']==True:
        voc_tools.setup_darknet_dataset(cfg_obj)
        darknet_scripts.write_anchors_from_yml_params(cfg_obj)

def darkflow_parse_config(cfg_obj):
    def add_optional(options,obj,name):
        if name in obj:
            options[name] = obj[name]
    darkflow_bin_folder = cfg_obj.darkflow_bin_path()
    yaml_options = {
        'model': cfg_obj.model_path(),
        'dataset': cfg_obj.images_path(),
        'annotation': cfg_obj.annotations_path(),
        'labels': cfg_obj.labels_filename(),
        'backup': darkflow_bin_folder + '/ckpt/',
        'imgdir': cfg_obj.images_path(),
        'bin': cfg_obj.bin_path(),
        'summary': cfg_obj.summary_path(),
        'train': False
    }
    cfg_train = cfg_obj.model_params()['train']
    add_optional(yaml_options,cfg_train,'epoch')
    if 'gpu' in cfg_train and (cfg_train['gpu']==True or cfg_train['gpu']=="true"):
        yaml_options['gpu'] = 1.0
    return yaml_options
    
def train_darkflow_model(cfg_obj,load_ckpt):
    options = darkflow_parse_config(cfg_obj)
    options['train'] = True
    if load_ckpt is not None:
        options['load'] = int(load_ckpt)

    tfnet = TFNet(options)
    tfnet.train()

def predict_darkflow_model(cfg_obj,args):
    options = darkflow_parse_config(cfg_obj)
    if args.load is None:
        raise AssertionError('Please provide a ckpt number to load from.')
    options['load'] = int(args.load)
    if args.threshold is not None:
        options['threshold'] = args.threshold

    tfnet = TFNet(options)
    tfnet.predict()
    # save in json format too
    options['json'] = True
    tfnet = TFNet(options)
    tfnet.predict()

def savepb_darkflow_model(cfg_obj,args):
    options = darkflow_parse_config(cfg_obj)
    if args.load is None:
        raise AssertionError('Please provide a ckpt number to load from.')
    options['load'] = int(args.load)

    tfnet = TFNet(options)
    tfnet.savepb()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Setup the files for training/testing')
    parser.add_argument('--config', type=str,
                        help='YAML file for config', required=True)
    parser.add_argument('--mode',
                        help='setup basic files', default='setup')
    parser.add_argument('--load', 
                        help='resumed from a previously trained point (-1 from the most recent)', 
                        default=None)
    parser.add_argument('--threshold', 
                        help='detection threshold', 
                        default=None)
    # parser.add_argument('--verbose', 
    #                     help='detection threshold', 
    #                     default=False)

    args = parser.parse_args()

    # read YAML
    cfg_obj = yolocfg.read_yaml_main_config(args.config)

    if args.mode=='setup':
        setup_darkflow_files(cfg_obj)
        exit('Finished setup.')

    # Import darkflow based on folder provided in yaml
    darkflow_folder = cfg_obj.darkflow_bin_path()
    sys.path.append(darkflow_folder)
    from darkflow.net.build import TFNet

    if args.mode=='train':
        train_darkflow_model(cfg_obj,args.load)
    elif args.mode=='predict':
        predict_darkflow_model(cfg_obj,args)
    elif args.mode=='savepb':
        savepb_darkflow_model(cfg_obj,args)
    else:
        raise RuntimeError('I do not recognize this mode')
