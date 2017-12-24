import unittest
import sys
import yaml
import os
import shutil

sys.path.append('../../darkflow_tools')
import parse_yolo_cfg as yolocfg
import voc_tools
import darknet_scripts

build_folder = os.path.abspath('../../../build/python/tests/deep_learning')
flow='{}/darkflow'.format(build_folder)
base_yml_params = {
    'dataset':{
        'dataset_folder':'{}/dataset'.format(build_folder),
        # 'tmp_folder':'{}/tmp'.format(build_folder), # undefined yet
        'darkflow_folder': flow
    },
    'model': {
        'model_path': './yolo_example.cfg',
        'train': {'epoch':1000000},
        'num_anchors': 7,
        'height':104,
        'width':104,
        'find_anchors': True,
        'classes':['wifi','generic_mod','square']
    }
}
yml_base = yaml.dump(base_yml_params,default_flow_style=False)

def make_dirs(cfg_params):
    def ensure_dir(dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    # dataset_dir = cfg_params['dataset']['dataset_folder']
    tmp_dir = cfg_params['dataset']['tmp_folder']
    flow_dir = cfg_params['dataset']['darkflow_folder']

    # ensure_dir(dataset_dir)
    ensure_dir(tmp_dir)
    ensure_dir(flow_dir)

def force_rmdir(path):
    # check if folder exists
    if os.path.exists(path):
         # remove if exists
         shutil.rmtree(path)

def remove_dirs(cfg_params):
    def ensure_rmdir(dirname):
        if os.path.exists(dirname):
            force_rmdir(dirname)
    # dataset_dir = cfg_params['dataset']['dataset_folder']
    tmp_dir = cfg_params['dataset']['tmp_folder']
    flow_dir = cfg_params['dataset']['darkflow_folder']
    # ensure_rmdir(dataset_dir)
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

    return yolo_cfg

class TestStringMethods(unittest.TestCase):
    def test_yaml_parser_no_files(self):
        # this should fail because functions do not exist
        yml1 = dict(base_yml_params)
        yml1['dataset']['tmp_folder'] = '{}/tmp1'.format(build_folder)
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml1)

    def test_yaml_parser_with_files(self):
        yml2 = dict(base_yml_params)
        yml2['dataset']['tmp_folder'] = '{}/tmp2'.format(build_folder)
        make_dirs(yml2)

        # this should not fail as the files exist
        # try:
        test_yaml_parser_generic(self,yml2)
        # finally:
        #     remove_dirs(yml2)

    def test_yaml_parser_wrong_params(self):
        '''
        This test checks if the parser finds inconsistencies
        between the model and yml
        '''
        yml3_1 = dict(base_yml_params)
        yml3_1['model']['classes'] = 3
        yml3_1['dataset']['tmp_folder'] = '{}/tmp3_1'.format(build_folder)
        make_dirs(yml3_1)
        yml3_2 = dict(base_yml_params)
        yml3_2['model']['num'] = 4
        yml3_2['dataset']['tmp_folder'] = '{}/tmp3_2'.format(build_folder)
        make_dirs(yml3_2)
        yml3_3 = dict(base_yml_params)
        yml3_3['model']['height'] = 1000
        yml3_3['dataset']['tmp_folder'] = '{}/tmp3_3'.format(build_folder)
        make_dirs(yml3_3)

        # it should fail as the yaml and cfg are not consistent
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml3_1)
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml3_2)
        with self.assertRaises(AssertionError):
            test_yaml_parser_generic(self,yml3_3)

        # remove_dirs(yml3_1)
        # remove_dirs(yml3_2)
        # remove_dirs(yml3_3)

    def test_darknet_annotations_generation(self):
        yml4 = dict(base_yml_params)
        yml4['dataset']['tmp_folder'] = '{}/tmp4'.format(build_folder)
        make_dirs(yml4)

        yml_cfg = test_yaml_parser_generic(self,yml4)
        voc_tools.setup_darknet_dataset(yml_cfg)

        assert os.path.isfile(yml_cfg.tmp_imgpaths_filename())
        # TODO: assert generated files make sense

        print yml_cfg.cfg_params
        # generate anchors
        darknet_scripts.write_anchors_from_yml_params(yml_cfg)

        # remove_dirs(yml4)

if __name__ == '__main__':
    unittest.main()

