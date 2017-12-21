import unittest
import sys
import yaml
import os

sys.path.append('../../darkflow_tools')
import parse_yolo_cfg as yolocfg

flow='./darkflow'
base_yml_params = {
    'dataset':{
        'dataset_folder':'./dataset',
        'tmp_folder':'./tmp',
        'darkflow_folder': flow
    },
    'model': {
        'model_path': './yolo_example.cfg',
        'train': {'epoch':1000000},
        'num_anchors': 5,
        'height':104,
        'width':104,
        'find_anchors': True,
        'classes':['wifi','PSK']
    }
}
yml_base = yaml.dump(base_yml_params,default_flow_style=False)

def make_dirs(cfg_params):
    def ensure_dir(dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    dataset_dir = cfg_params['dataset']['dataset_folder']
    tmp_dir = cfg_params['dataset']['tmp_folder']
    flow_dir = cfg_params['dataset']['darkflow_folder']

    ensure_dir(dataset_dir)
    ensure_dir(tmp_dir)
    ensure_dir(flow_dir)

def remove_dirs(cfg_params):
    def ensure_rmdir(dirname):
        if os.path.exists(dirname):
            os.rmdir(dirname)
    dataset_dir = cfg_params['dataset']['dataset_folder']
    tmp_dir = cfg_params['dataset']['tmp_folder']
    flow_dir = cfg_params['dataset']['darkflow_folder']
    ensure_rmdir(dataset_dir)
    ensure_rmdir(tmp_dir)
    ensure_rmdir(flow_dir)

def test_yaml_parser_generic(unittester,yml_params):
    yml_str = yaml.dump(yml_params,default_flow_style=False)

    # it may fail here
    yolo_cfg = yolocfg.YOLOCfgPaths(yaml.load(yml_str))

    # check fields
    dataset_path = os.path.abspath(base_yml_params['dataset']['dataset_folder'])
    tmp_path = os.path.abspath(base_yml_params['dataset']['tmp_folder'])
    unittester.assertEqual(yolo_cfg.dataset_path(),dataset_path)
    unittester.assertEqual(yolo_cfg.tmp_path(),tmp_path)

class TestStringMethods(unittest.TestCase):
    def test_yaml_parser_no_files(self):
        # this should fail because functions do not exist
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,base_yml_params)

    def test_yaml_parser_with_files(self):
        make_dirs(base_yml_params)

        # this should not fail as the files exist
        try:
            test_yaml_parser_generic(self,base_yml_params)
        finally:
            remove_dirs(base_yml_params)

    def test_yaml_parser_wrong_params(self):
        yml1 = dict(base_yml_params)
        yml1['model']['classes'] = 3
        yml2 = dict(base_yml_params)
        yml2['model']['num'] = 4
        yml3 = dict(base_yml_params)
        yml3['model']['height'] = 1000
        make_dirs(yml1)

        # it should fail as the yaml and cfg are not consistent
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml1)
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml2)
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml3)
        remove_dirs(yml1)

if __name__ == '__main__':
    unittest.main()

