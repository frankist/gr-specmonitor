import yaml
import os
import ConfigParser

class YOLOCfgPaths:
    img_foldername = 'JPEGImages'
    annotations_foldername = 'Annotations'
    darknet_annotations_foldername = 'labels'

    def __init__(self,cfg_params):
        self.cfg_params = cfg_params
        self.assert_validity()

    def assert_validity(self):
        assert_yaml_cfg_correctness(self.cfg_params)

    def dataset_path(self):
        return os.path.abspath(self.cfg_params['dataset']['dataset_folder'])

    def images_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.img_foldername)

    def annotations_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.annotations_foldername)

    def darknet_annotations_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.darknet_annotations_foldername)

    def tmp_path(self):
        return os.path.abspath(self.cfg_params['dataset']['tmp_folder'])

    def tmp_imgpaths_filename(self):
        return '{}/{}'.format(self.tmp_path(),'dataset_img_paths.txt')

    def labels_file(self):
        return '{}/{}'.format(self.tmp_path(),'labels.txt')

    def model_params(self):
        return self.cfg_params['model_params']

def read_yaml_main_config(filename):
    with open(filename,'r') as f:
        cfg_params = yaml.load(f)
    return YOLOCfgPaths(cfg_params)

def assert_yaml_cfg_correctness(cfg_params):
    assert 'dataset' in cfg_params
    dataset = cfg_params['dataset']
    assert 'tmp_folder' in dataset
    assert 'dataset_folder' in dataset
    assert 'darkflow_folder' in dataset
    assert os.path.exists(dataset['tmp_folder'])
    assert os.path.exists(dataset['dataset_folder'])
    assert os.path.exists(dataset['darkflow_folder'])
    assert 'model_path' in cfg_params['model']
    assert os.path.isfile(cfg_params['model']['model_path'])
    # TODO: check if img and annotations folders exist

    assert_darknet_params_correctness(cfg_params)

def assert_darknet_params_correctness(cfg_params):
    model_params = cfg_params['model']

    # read cfg file
    cfgparser = ConfigParser.ConfigParser()
    cfgparser.read(model_params['model_path'])

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
    if num_filters!=5*(num_anchors+num_classes):
        raise AssertionError('ERROR: Set the number of filters in the last conv layer to {}'.format(5*(num_anchors+num_classes)))

    # TODO: check if the number of anchors is equal to num
