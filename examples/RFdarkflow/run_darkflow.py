import sys
sys.path.append('../../python/darkflow_tools')
import argparse
import os
import subprocess
import cv2

import parse_yolo_cfg as yolocfg
from darkflow.net.build import TFNet
import voc_tools
import darknet_scripts

def current_train_step(backup_folder):
    checkpoint_fname = os.path.join(backup_folder,'checkpoint')
    if not os.path.isfile(checkpoint_fname):
        return -1
    with open(os.path.join(backup_folder,'checkpoint'), 'r') as f:
        last = f.readlines()[-1].strip()
        load_point = last.split(' ')[1]
        load_point = load_point.split('"')[1]
        load_point = load_point.split('-')[-1]
        load_number = int(load_point)
    return load_number

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
    yaml_options = {
        'model': cfg_obj.model_path(),
        'dataset': cfg_obj.images_path(),
        'annotation': cfg_obj.annotations_path(),
        'labels': cfg_obj.labels_filename(),
        'backup': cfg_obj.backup_path(),
        'imgdir': cfg_obj.images_path(),
        'bin': cfg_obj.bin_path(),
        'summary': cfg_obj.summary_path(),
        'train': False
    }
    cfg_train = cfg_obj.model_params()['train']

    # parse darkflow args directly
    for k,v in cfg_obj.cfg_params['darkflow'].items():
        yaml_options[k] = v

    return yaml_options

class DarkflowTrainer:
    def __init__(self,yaml_cfg,args):
        self.current_epoch = 0
        # parse the YAML
        self.yaml_cfg = yaml_cfg
        self.base_options = darkflow_parse_config(self.yaml_cfg)
        self.base_options['train'] = True
        self.batch_size = self.base_options.get('batch',16)

        # get dataset info
        from darkflow.utils.pascal_voc_clean_xml import pascal_voc_clean_xml
        dumps = pascal_voc_clean_xml(self.base_options['annotation'], self.base_options['labels'], False)
        #tfnet = TFNet(self.base_options)
        #self.dataset_size = len(tfnet.framework.parse())
        self.dataset_size = len(dumps)
        self.steps_per_epoch = self.dataset_size/self.batch_size

        # parse the ckpt
        self.load_ckpt = args.load
        current_step = 0
        if self.load_ckpt is not None:
            self.base_options['load'] = args.load
            if self.load_ckpt == 'best':
                # load the best result so far.
                from darkflow.net.flow import BestModelStats
                backup_path = yaml_cfg.backup_path()
                model_name = os.path.basename(os.path.splitext(self.base_options['model'])[0]) + '-best_stats.yaml'
                yaml_fname = os.path.join(backup_path, model_name)
                model_stats = BestModelStats.load(yaml_fname)
                current_step = model_stats.point_min[0]
                if current_step<0:
                    AssertionError('There is no best model yet stored.')
            else:
                # loads a specified number or last (-1)
                self.base_options['load'] = int(self.base_options['load'])
                current_step = int(self.load_ckpt)
                if current_step < 0:
                    current_step = current_train_step(self.base_options['backup'])
        self.current_epoch = current_step/self.steps_per_epoch

        # configure the trainer
        self.cfg_train = yaml_cfg.model_params()['train']
        self.total_epochs = self.cfg_train['total_epochs']
        self.train_steps = self.cfg_train.get('epoch_steps',[0])
        if 'lr' in self.base_options:
            self.lr_steps = [float(self.base_options['lr'])]
        else:
            self.lr_steps = [float(i) for i in self.cfg_train.get('lr',[1.0e-5])]
        assert len(self.lr_steps)==len(self.train_steps)
        #self.momentum_steps = [float(i) for i in self.cfg_train.get('momentum',[0.0]*len(self.train_steps))]

        # parse the args
        if args.trainer is not None:
            self.base_options['trainer'] = args.trainer
        if args.gpu is not None:
            self.base_options['gpu'] = float(args.gpu)

    def train_phase(self):
        phase_idx = [i for i in range(len(self.train_steps)) if self.train_steps[i]<=self.current_epoch][-1]
        lr = self.lr_steps[phase_idx]
        upper_epoch = self.train_steps[phase_idx+1] if phase_idx<len(self.train_steps)-1 else self.total_epochs
        number_of_epochs = upper_epoch - self.current_epoch

        print("====== Start of a new training phase ======")
        print("Learning Rate: {}".format(lr))
        print("Number of epochs: {}".format(number_of_epochs))
        #print("Momentum: {}".format(self.momentum_steps[phase_idx]))
        print("===========================================")

        # set args for new phase
        options = dict(self.base_options)
        if self.current_epoch>0:
            assert 'load' in options
        options['lr'] = lr
        #options['momentum'] = self.momentum_steps[phase_idx]
        options['epoch'] = number_of_epochs

        # train
        tfnet = TFNet(options)
        tfnet.train()
        self.current_epoch += number_of_epochs

    def train(self):
        print('These are the learning rates that I am gonna use.',self.lr_steps)
        print('We are at the epoch {} of a total of {}'.format(self.current_epoch,self.total_epochs))
        while self.current_epoch < self.total_epochs:
            self.train_phase()

def predict_darkflow_model(cfg_obj,args):
    options = darkflow_parse_config(cfg_obj)
    
    # erase previous predictions
    imgdir_path = options['imgdir']
    out_dir = os.path.join(imgdir_path,'out')
    for the_file in os.listdir(out_dir):
        file_path = os.path.join(out_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    # load args
    if args.load is None:
        raise AssertionError('Please provide a ckpt number to load from.')
    options['load'] = args.load if args.load=='best' else int(args.load)
    if args.threshold is not None:
        options['threshold'] = float(args.threshold)
    if args.gpu is not None:
        options['gpu'] = float(args.gpu)

    tfnet = TFNet(options)
    tfnet.predict()
    # save in json format too
    options['json'] = True
    tfnet = TFNet(options)
    assert tfnet.FLAGS.threshold>=0
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
                        default=0.6)
    parser.add_argument('--trainer',help='trainer time (e.g. adam)', default=None)
    parser.add_argument('--gpu',help='use GPU', default=None)
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
    # darkflow_folder = cfg_obj.darkflow_bin_path()
    # sys.path.append(darkflow_folder)
    # from darkflow.net.build import TFNet

    if args.mode=='train':
        trainer = DarkflowTrainer(cfg_obj,args)
        trainer.train()
    elif args.mode=='predict':
        predict_darkflow_model(cfg_obj,args)
    elif args.mode=='savepb':
        savepb_darkflow_model(cfg_obj,args)
    else:
        raise RuntimeError('I do not recognize this mode')
