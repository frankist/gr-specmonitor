from future import standard_library
standard_library.install_aliases()
from builtins import object
import yaml
import os
import configparser
import shutil

# helper
def try_mkdir(path):
    if not os.path.exists(path):
        if os.path.isfile(path):
            raise RuntimeError('The path {} is an existing file'.format(path))
        os.mkdir(path)

class DarkflowArgs(object): # to replace YOLOCfgPaths in the future
    option_types = {'batch':int,
                    'gpu':float,
                    'lr':float,
                    'trainer':str,
                    'threshold':float,
                    'momentum':float,
                    'dataset':str,
                    'load':None,
                    'model':str,
                    'dataset':str,
                    'annotation':str,
                    'imgdir':str,
                    'labels':str,
                    'backup':str,
                    'bin':str,
                    'summary':str}
    img_foldername = 'Images'#'JPEGImages'
    annotations_foldername = 'Annotations'
    def __init__(self):
        # train/predict params (setting defaults here)
        # NOTE: None means darkflow default
        self.batch = 16
        self.gpu = 0.0
        self.lr = 1.0e-5
        self.trainer = None
        self.threshold = None
        self.momentum = 0.9
        self.train = False

    def try_setattr(self,name,value,type_cast=None,must_exist=True):
        if value is not None: # overwrites if specified.
            if type_cast is None:
                if name in DarkflowArgs.option_types:
                    if DarkflowArgs.option_types[name] is None:
                        setattr(self,name,value)
                    else:
                        setattr(self, name, DarkflowArgs.option_types[name](value)) # cast
                elif must_exist:
                    raise AttributeError('The argument {} is not supported'.format(name)) 
                #    #setattr(self, name, value) # no cast
            else:
                setattr(self, name, type_cast(value)) # specified cast

    def parse_yaml(self,yaml_path,yaml_dict):
        # real file
        #if isinstance(yaml_file,str):
        #    with open(yaml_file,'r') as f:
        #        yaml_dict = yaml.load(f)
        #    yaml_path = os.path.dirname(os.path.abspath(yaml_file))

        def abspath(relative_path):
            return os.path.normpath(os.path.join(yaml_path,relative_path))

        # set paths
        dataset_path = abspath(yaml_dict['dataset']['dataset_folder'])
        tmp_path = abspath(yaml_dict['dataset']['tmp_folder'])
        model_path = abspath(yaml_dict['model']['model_path'])
        self.set_paths(model_path,dataset_path,tmp_path)

        # set darkflow args
        darkflow_args = yaml_dict['darkflow']
        for k,v in darkflow_args.items():
            self.try_setattr(k,v,DarkflowArgs.option_types[k])
        
    def set_paths(self,model_path,dataset_dir,tmp_dir):
        model_path = os.path.abspath(os.path.expanduser(model_path))
        self.try_setattr('model',model_path)
        # dataset folder
        dataset_path = os.path.abspath(os.path.expanduser(dataset_dir))
        self.try_setattr('dataset',dataset_path)
        annotation_path = os.path.join(dataset_path,DarkflowArgs.annotations_foldername)
        self.try_setattr('annotation',annotation_path)
        imgdir_path = os.path.join(dataset_path,DarkflowArgs.img_foldername)
        self.try_setattr('imgdir',imgdir_path)

        # tmp folder
        tmp_path = os.path.abspath(os.path.expanduser(tmp_dir))
        labels_path = os.path.join(tmp_path,'labels.txt')
        self.try_setattr('labels',labels_path)
        backup_path = os.path.join(tmp_path,'ckpt')
        self.try_setattr('backup',backup_path)
        bin_path = os.path.join(tmp_path,'bin')
        self.try_setattr('bin',bin_path)
        summary_path = os.path.join(tmp_path,'summary')
        self.try_setattr('summary',summary_path)
        
    def parse_cmdline(self,cmd_args):
        if not isinstance(cmd_args,dict):
            options = vars(cmd_args)
        else:
            options = cmd_args
        for name,value in options.items():
            if name.startswith('__') or name=='mode': # it is private #FIXME
                continue
            self.try_setattr(name,value,must_exist=False)
        
    def generate_args(self,assert_train_paths=True):
        assert_paths_exist(self,assert_train_paths)
        options = vars(self)
        for k,v in options.items():
            if v is None: # Remove any None
                del options[k]
        return options

def assert_paths_exist(cfg_obj,assert_train_paths=True):
    def assert_path_exists(path,check_file=False):
        test = not os.path.exists(path)
        test |= check_file and not os.path.isfile(path)
        if test:
            raise AssertionError('Path {} does not exist.'.format(path))
    # assert all paths exist
    assert_path_exists(cfg_obj.model)
    assert_path_exists(cfg_obj.labels)
    if assert_train_paths:
        assert_path_exists(cfg_obj.dataset)
        assert_path_exists(cfg_obj.annotation)
        assert_path_exists(cfg_obj.imgdir)
        assert_path_exists(cfg_obj.backup)
        assert_path_exists(cfg_obj.bin)
        assert_path_exists(cfg_obj.summary)

class DarkflowConfig(object):
    darknet_annotations_foldername = 'darknet_annotations'
    def __init__(self):
        self.yaml_params = {}
        self.yaml_file = ''
        self.args = None
    
    def setup(self,yaml_file,cmdline_args):
        with open(yaml_file,'r') as f:
            self.yaml_params = yaml.load(f)
        self.yaml_file = os.path.abspath(yaml_file)
        self.args = DarkflowArgs()
        self.args.parse_yaml(os.path.dirname(self.yaml_file),self.yaml_params)
        self.args.parse_cmdline(cmdline_args)
        self.setup_paths()
        
    def tmp_path(self):
        return os.path.basename(self.args.backup)

    def darknet_annotations_path(self):
        return os.path.join(self.tmp_path(),DarkflowConfig.darknet_annotations_foldername)

    def setup_paths(self):
        # setup tmp folder which is going to be used as output
        try_mkdir(self.tmp_path())
        # setup ckpt folder
        try_mkdir(self.args.backup)
        # make out dir inside images
        try_mkdir(os.path.join(self.args.imgdir,'out'))
    
    def generate_args(self,assert_train_paths=True):
        return self.args.generate_args(assert_train_paths)

def assert_config_correctness():
    # assert param correctness
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

class YOLOCfgPaths(object):
    img_foldername = 'Images'#'JPEGImages'
    annotations_foldername = 'Annotations'
    darknet_annotations_foldername = 'darknet_annotations'

    def __init__(self,yml_cfg_args, yml_file):
        """
        Receives the parsed YAML parameters, and the name of the yaml file
        """
        self.yml_filepath = os.path.abspath(yml_file)
        self.cfg_params = dict(yml_cfg_args)
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
    """
    Reads a YAML file with the configuration of the YOLO network
    """
    with open(filename,'r') as f:
        cfg_args = yaml.load(f)
    return YOLOCfgPaths(cfg_args, filename)

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
