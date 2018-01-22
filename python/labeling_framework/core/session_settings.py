
def init():
    """ Initialize global variables """
    global registered_tasks
    registered_tasks = {}

def register_task_handler(name, ClassPtr):
    registered_tasks[name] = ClassPtr

def retrieve_task_handler(name):
    return registered_tasks[name]
