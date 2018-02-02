import shutil
import os
import yaml
import argparse

def create_new_model():
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

def save_ckpt_model():
    import zlib
    def assert_exists(path):
        if not os.path.exists(path):
            raise AssertionError('The path {} does not exist!'.format(path))
    model_name = raw_input("Name of model to save?")

    # check folder
    model_path = '../tmp/RFdarkflow_{}'.format(model_name)
    assert_exists(model_path)
    model_cfg_fname = 'yolo_{}.cfg'.format(model_name)
    model_cfg_fname = os.path.join(model_path,model_cfg_fname)
    assert_exists(model_cfg_fname)
    yml_fname = os.path.join(model_path,'yolo_train_{}.yml'.format(model_name))
    assert_exists(yml_fname)
    label_fname = os.path.join(model_path,'labels.txt')
    assert_exists(label_fname)
    ckpt_folder = os.path.join(model_path,'ckpt')
    assert_exists(ckpt_folder)
    checkpoint_fname = os.path.join(ckpt_folder,'checkpoint')
    assert_exists(checkpoint_fname)
    number_pos = len('yolo_{}-'.format(model_name))
    fmt = 'yolo_{}-*.*'.format(model_name)

    # check ckpt folder
    most_recent_ckpt = []
    max_n = -1
    for f in os.listdir(ckpt_folder):
        if not f.find('yolo_{}-'.format(model_name)): # could be checkpoint
            continue
        dot_pos = f[number_pos::].find('.')
        n = int(f[number_pos:(number_pos+dot_pos)])
        if n>max_n:
            max_n = n
            most_recent_ckpt = [f]
        elif n==max_n:
            most_recent_ckpt.append(f)
    print('Most recent ckpt number is {}. Going to save it'.format(n))
    assert(len(most_recent_ckpt)==4)

    # compress files into a zip
    dst = os.path.join(model_path,'save')
    ckpt_dst = os.path.join(dst,'ckpt')
    assert(not os.path.exists(dst))
    os.mkdir(dst)
    os.mkdir(ckpt_dst)
    def cp_file(fpath,dstfolder):
        shutil.copy2(fpath,os.path.join(dstfolder,os.path.basename(fpath)))
    cp_file(model_cfg_fname,dst)
    cp_file(yml_fname,dst)
    cp_file(label_fname,dst)
    cp_file(checkpoint_fname,ckpt_dst)
    for f in most_recent_ckpt:
        cp_file(os.path.join(ckpt_folder,f),ckpt_dst)
    print 'Success at saving model number {}'.format(max_n)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Create new darkflow models.')
    parser.add_argument('--cmd', help='Choose one command (add/save)')

    args = parser.parse_args()
    print('Received command: {}'.format(args.cmd))

    if args.cmd=='add':
        create_new_model()
    elif args.cmd=='save':
        save_ckpt_model()
    else:
        raise NotImplementedError('I do not recognize such command.')
