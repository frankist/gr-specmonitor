
def init():
    """ Initialize global variables """
    global registered_tasks
    registered_tasks = {} # We register here all the types of concrete tasks
    global task_dependency_tree
    task_tree = {} # We register here the dependency tree graph
    global global_settings
    global_settings = {}
    global stage_settings
    stage_settings = {}

def register_task_handler(name, ClassPtr):
    registered_tasks[name] = ClassPtr

def retrieve_task_handler(name):
    return registered_tasks[name]

def retrieve_task_handlers():
    return registered_tasks

def set_task_dependency_tree(dtree):
    assert isinstance(dtree,dict)
    global task_tree
    task_tree = dtree

def get_task_dependency_tree():
    return dict(task_tree)

def set_stage_setting(stage_name,variable,value):
    if stage_name in stage_settings:
        assert stage_name in registered_tasks
        stage_settings[stage_name] = {}
    stage_settings[stage_name][variable] = value

def get_stage_setting(stage_name,variable):
    return stage_settings[stage_name][variable]
