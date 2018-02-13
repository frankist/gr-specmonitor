import os

from . import session_settings

def session_dir():
    return session_settings.session_args.session_path

def session_params_file():
    return session_settings.session_args.cfg_file

def stage_dir(stage_name):
    return os.path.join(session_dir(),stage_name)

def tmp_dir():
    return os.path.join(session_dir(),'tmp')

def session_pkl():
    return os.path.join(session_dir(),'param_cfg2.pkl')

def remote_session_dir():
    return '~/{}'.format(session_settings.session_name())

def stage_result_file(stage_name,fidxt_list,fmt='.pkl'):
    folder = os.path.join(session_dir(),stage_name)
    filename = 'data_' + '_'.join([str(i) for i in fidx_list])
    return os.path.join(folder,filename+fmt)
