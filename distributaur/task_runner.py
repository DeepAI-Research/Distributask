# distributaur/task_runner.py

from celery import Celery, Task
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
from distributaur.utils import get_redis_connection, get_redis_values
from distributaur.config import config

app = None
registered_functions = {}

class CallFunctionTask(Task):
    name = 'call_function'

    def run(self, func_name, args_json):
        """
        Handle a task by executing the registered function with the provided arguments.

        Args:
            func_name (str): The name of the registered function to execute.
            args_json (str): The JSON string representation of the arguments for the function.
        """
        print(f"Received task with function: {func_name}, and args: {args_json}")
        if func_name not in registered_functions:
            print("registered_functions are", registered_functions)
            raise ValueError(f"Function '{func_name}' is not registered.")

        func = registered_functions[func_name]
        args = json.loads(args_json)

        print(f"Executing task with function: {func_name}, and args: {args}")
        result = func(**args)
        update_function_status(self.request.id, "completed")
        return result

def configure(**kwargs):
    global app
    config.configure(**kwargs)
    redis_url = get_redis_values(config)
    app = Celery(
        "distributaur", broker=redis_url, backend=redis_url
    )
    
    # Register call_function as a task
    app.tasks.register(CallFunctionTask())
    print("Celery configured.")

def register_function(func):
    """Decorator to register a function in the dictionary."""
    registered_functions[func.__name__] = func
    return func

def execute_function(func_name, args):
    """
    Execute a task by passing the function name and arguments.

    Args:
        func_name (str): The name of the registered function to execute.
        args (dict): The dictionary of arguments for the function.
    """
    args_json = json.dumps(args)
    print(f"Dispatching task with function: {func_name}, and args: {args_json}")
    return app.send_task('call_function', args=[func_name, args_json])

def update_function_status(task_id, status):
    """
    Update the status of a task in Redis.

    Args:
        task_id (str): The ID of the task.
        status (str): The new status of the task.
    """
    redis_client = get_redis_connection(config)
    redis_client.set(f"task_status:{task_id}", status)
