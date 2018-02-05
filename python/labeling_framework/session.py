import sys
import luigi
import logging

from labeling_framework.core import session_settings
from labeling_framework.core.LuigiSimulatorHandler import *
from labeling_framework.utils import logging_utils
logger = logging_utils.DynamicLogger(__name__)

def find_declared_tasks(parent_task=StageLuigiTask):
    child_tasks = parent_task.__subclasses__()
    concrete_child_tasks = []
    for c in child_tasks:
        if c.is_concrete():#not inspect.isabstract(c):
            concrete_child_tasks.append(c)
        else:
            concrete_child_tasks += find_declared_tasks(c)
    return concrete_child_tasks

def init():
    session_settings.init()

    # set up logging
    logging_utils.addLoggingLevel('TRACE',logging.WARNING-5)

    # register the declared tasks
    child_tasks = find_declared_tasks()
    for task in child_tasks:
        session_settings.register_task_handler(task.my_task_name(), task)

    # produce the Task Dependency Tree
    dtree = {}
    for name,task in session_settings.retrieve_task_handlers().items():
        dep = task.depends_on()
        if dep is not None:
            if isinstance(dep,basestring):
                dep = session_settings.retrieve_task_handler(dep)
            dtree[task.my_task_name()] = dep.my_task_name()
    session_settings.set_task_dependency_tree(dtree)

    # call task setup for every task type
    for name,task in session_settings.retrieve_task_handlers().items():
        task.setup()

def run(session):
    init()
    # cmdline_args = ['OTACmdSession','--local-scheduler']
    luigi.run(main_task_cls=session, local_scheduler=True)#cmdline_args)
