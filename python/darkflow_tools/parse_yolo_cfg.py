import yaml
import os
import ConfigParser

class YOLOCfgPaths:
    img_foldername = 'JPEGImages'
    annotations_foldername = 'Annotations'
    darknet_annotations_foldername = 'darknet_annotations'

    def __init__(self,cfg_params):
        self.cfg_params = dict(cfg_params)
        self.assert_validity()

    def assert_validity(self):
        assert_yaml_cfg_correctness(self)

    def dataset_path(self):
        return os.path.abspath(os.path.expanduser(self.cfg_params['dataset']['dataset_folder']))

    def images_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.img_foldername)

    def annotations_path(self):
        return '{}/{}'.format(self.dataset_path(),YOLOCfgPaths.annotations_foldername)

    def darknet_annotations_path(self):
        return '{}/{}'.format(self.tmp_path(),YOLOCfgPaths.darknet_annotations_foldername)

    def tmp_path(self):
        return os.path.abspath(os.path.expanduser(self.cfg_params['dataset']['tmp_folder']))

    def tmp_imgpaths_filename(self):
        return '{}/{}'.format(self.tmp_path(),'dataset_img_paths.txt')

    def labels_filename(self):
        return '{}/{}'.format(self.tmp_path(),'labels.txt')

    def model_params(self):
        return self.cfg_params['model']

    def model_path(self):
        return os.path.abspath(os.path.expanduser(self.cfg_params['model']['model_path']))

    def darkflow_bin_path(self):
        return os.path.abspath(os.path.expanduser(self.cfg_params['dataset']['darkflow_folder']))

    def summary_path(self):
        return '{}/{}'.format(self.tmp_path(),'summary')

    def bin_path(self):
        return '{}/{}'.format(self.tmp_path(),'bin')

    def backup_path(self):
        return '{}/{}'.format(self.tmp_path(),'backup_path')

def read_yaml_main_config(filename):
    with open(filename,'r') as f:
        cfg_params = yaml.load(f)
    return YOLOCfgPaths(cfg_params)

def assert_yaml_cfg_correctness(yolo_cfg):
    cfg_params = yolo_cfg.cfg_params
    def assert_path_exists(path):
        if not os.path.exists(path):
            raise AssertionError('Path {} does not exist.'.format(path))

    assert 'dataset' in cfg_params
    dataset = cfg_params['dataset']
    assert 'tmp_folder' in dataset
    assert 'dataset_folder' in dataset
    assert 'darkflow_folder' in dataset
    assert_path_exists(yolo_cfg.dataset_path())
    assert_path_exists(yolo_cfg.tmp_path())
    assert_path_exists(yolo_cfg.darkflow_bin_path())
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
    expected_num_filters = num_anchors*(num_classes+5)
    if num_filters!=expected_num_filters:
        raise AssertionError('ERROR: Set the number of filters in the last conv layer to {}'.format(expected_num_filters))

    # TODO: check if the number of anchors is equal to num
