from future import standard_library
standard_library.install_aliases()
from builtins import object
from labeling_framework.utils.filesystem_utils import *
import yaml
import os
import configparser
import shutil

class YOLOCfgPaths(object):
    img_foldername = 'Images'#'JPEGImages'
    annotations_foldername = 'Annotations'
    darknet_annotations_foldername = 'darknet_annotations'

    def __init__(self,cfg_params, yml_file):
        self.yml_filepath = os.path.abspath(yml_file)
        self.cfg_params = dict(cfg_params)
        self.yml_path = os.path.dirname(self.yml_filepath)
        self.setup_paths()
        self.assert_validity()

    def abspath(self, relative_path):
        return os.path.normpath(os.path.join(self.yml_path, relative_path))

    def assert_validity(self):
        assert_yaml_cfg_correctness(self)

    def setup_paths(self):
        # setup tmp folder which is going to be used as output
        try_mkdir(self.tmp_path())
        # setup ckpt folder
        try_mkdir(os.path.join(self.tmp_path(),'ckpt'))
        # make out dir inside images
        try_mkdir(os.path.join(self.images_path(),'out'))
        # # copy yaml file to tmp
        # shutil.copy2(self.yml_filepath,self.tmp_path())
        # # copy model file to tmp
        # shutil.copy2(self.model_path(),self.tmp_path())
        # print('Copies of the YAML and model files were placed in {}'.self.tmp_path())

    def dataset_path(self):
        return self.abspath(os.path.expanduser(self.cfg_params['dataset']['dataset_folder']))

    def images_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.img_foldername)

    def annotations_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.annotations_foldername)

    def darknet_annotations_path(self):
        return '{}/{}'.format(self.tmp_path(),YOLOCfgPaths.darknet_annotations_foldername)

    def tmp_path(self):
        return self.abspath(os.path.expanduser(self.cfg_params['dataset']['tmp_folder']))

    def tmp_imgpaths_filename(self):
        return '{}/{}'.format(self.tmp_path(),'dataset_img_paths.txt')

    def labels_filename(self):
        return '{}/{}'.format(self.tmp_path(),'labels.txt')

    def model_params(self):
        return self.cfg_params['model']

    def model_path(self):
        return self.abspath(os.path.expanduser(self.cfg_params['model']['model_path']))

    # def darkflow_bin_path(self):
    #     return self.abspath(os.path.expanduser(self.cfg_params['dataset']['darkflow_folder']))

    def summary_path(self):
        return '{}/{}'.format(self.tmp_path(),'summary')

    def bin_path(self):
        return '{}/{}'.format(self.tmp_path(),'bin')

    def backup_path(self):
        return '{}/{}'.format(self.tmp_path(),'ckpt')

def read_yaml_main_config(filename):
    with open(filename,'r') as f:
        cfg_params = yaml.load(f)
    return YOLOCfgPaths(cfg_params,filename)

def assert_yaml_cfg_correctness(yolo_cfg):
    cfg_params = yolo_cfg.cfg_params
    def assert_path_exists(path,check_file=False):
        test = not os.path.exists(path)
        test |= check_file and not os.path.isfile(path)
        if test:
            raise AssertionError('Path {} does not exist.'.format(path))

    assert 'dataset' in cfg_params
    dataset = cfg_params['dataset']
    assert 'tmp_folder' in dataset
    assert 'dataset_folder' in dataset
    # assert 'darkflow_folder' in dataset
    assert_path_exists(yolo_cfg.dataset_path())
    assert_path_exists(yolo_cfg.tmp_path())
    # assert_path_exists(yolo_cfg.darkflow_bin_path())
    assert 'model_path' in cfg_params['model']
    assert_path_exists(yolo_cfg.model_path(),True)
    # TODO: check if img and annotations folders exist

    assert_darknet_params_correctness(yolo_cfg)

def assert_darknet_params_correctness(yolo_cfg):
    cfg_params = yolo_cfg.cfg_params
    model_params = cfg_params['model']

    # read cfg file
    cfgparser = configparser.ConfigParser(strict=False)
    cfgparser.read(yolo_cfg.model_path())

    # assert height/width correctness
    w = cfgparser.getint('net','width')
    h = cfgparser.getint('net','height')
    assert w==model_params['width'] and h==model_params['height']

    # assert num of classes is consistent
    num_classes = cfgparser.getint('region','classes')
    if num_classes != len(model_params['classes']):
        raise AssertionError('ERROR: Make sure the num of classes in the model cfg file is the same as in the yaml file')

    # assert the number of anchors is consistent
    num_anchors = cfgparser.getint('region','num')
    if num_anchors != model_params['num_anchors']:
        raise AssertionError('ERROR: Make sure the num of anchors in the model cfg file is the same as in the yaml file')

    # assert that the number of filters is correct
    # NOTE: last convolutional layer wins in the parsing
    num_filters = cfgparser.getint('convolutional','filters')
    expected_num_filters = num_anchors*(num_classes+5)
    if num_filters!=expected_num_filters:
        raise AssertionError('ERROR: Set the number of filters in the last conv layer to {}'.format(expected_num_filters))

    # TODO: check if the number of anchors is equal to num

def generate_darkflow_args(cfg_obj):
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
    add_optional(yaml_options,cfg_train,'epoch')
    if 'gpu' in cfg_train:
        yaml_options['gpu'] = float(cfg_train['gpu'])
    if 'threshold' in cfg_train:
        yaml_options['threshold'] = float(cfg_train['threshold'])
    return yaml_options
