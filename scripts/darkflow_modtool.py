import shutil
import os
import yaml

if __name__=='__main__':

    model_name = raw_input("What name to give to the model?")

    # create a new folder in tmp
    src = '../examples/RFdarkflow'
    dst = '../tmp/RFdarkflow_{}'.format(model_name)
    if os.path.exists(dst):
        raise RuntimeError('The folder {} already exists'.format(dst))
    os.mkdir(dst)
    shutil.copy2(os.path.join(src,'yolo_train.yml'),dst)
    shutil.copy2(os.path.join(src,'yolo_model.cfg'),dst)
    # shutil.copytree(src,dst)

    # change the model's file name
    model_fname = 'yolo_{}.cfg'.format(model_name)
    src_model_fname = os.path.join(dst,'yolo_model.cfg')
    dst_model_fname = os.path.join(dst,model_fname)
    os.rename(src_model_fname,dst_model_fname)

    # change the training yml
    src_yml_fname = os.path.join(dst,'yolo_train.yml')
    dst_yml_fname = os.path.join(dst,'yolo_train_{}.yml'.format(model_name))
    os.rename(src_yml_fname,dst_yml_fname)

    # change the paths inside the yml
    with open(dst_yml_fname,'r') as f:
        cfg_params = yaml.load(f)
    cfg_params['dataset']['tmp_folder'] = './'
    cfg_params['model']['model_path'] = './{}'.format(model_fname)
    prev_folder = os.path.abspath(os.path.join(src,cfg_params['dataset']['dataset_folder']))
    dataset_folder = os.path.relpath(prev_folder,dst)
    cfg_params['dataset']['dataset_folder'] = dataset_folder
    with open(dst_yml_fname,'w') as f:
        yaml.dump(cfg_params, f, default_flow_style=False)

