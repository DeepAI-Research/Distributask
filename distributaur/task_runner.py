from celery import Celery
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
from distributaur.utils import get_redis_connection, get_redis_values

redis_url = get_redis_values()
app = Celery(
    "distributaur", broker=redis_url, backend=redis_url
)

registered_functions = {}

def register_function(func):
    """Decorator to register a function in the dictionary."""
    registered_functions[func.__name__] = func
    return func

@app.task
def call_function(func_name, args_json):
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
    update_function_status(call_function.request.id, "completed")
    return result

def execute_function(func_name, args):
    """
    Execute a task by passing the function name and arguments.

    Args:
        func_name (str): The name of the registered function to execute.
        args (dict): The dictionary of arguments for the function.
    """
    args_json = json.dumps(args)
    print(f"Dispatching task with function: {func_name}, and args: {args_json}")
    return call_function.delay(func_name, args_json)

def update_function_status(task_id, status):
    """
    Update the status of a task in Redis.

    Args:
        task_id (str): The ID of the task.
        status (str): The new status of the task.
    """
    redis_client = get_redis_connection()
    redis_client.set(f"task_status:{task_id}", status)
