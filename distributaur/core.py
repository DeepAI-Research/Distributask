# distributaur/task_runner.py
from celery import Celery
import os
import sys
import json
import os
import redis
from redis import ConnectionPool

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

app = None
registered_functions = {}
pool = None


def get_env_vars(path=".env.default"):
    env_vars = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                env_vars[key] = value
    return env_vars


class Config:
    def __init__(self):
        self.settings = {}
        self.settings.update(get_env_vars())

    def configure(self, **kwargs):
        self.settings.update(kwargs)

    def get(self, key, default=None):
        return self.settings.get(key, default)


config = Config()


def get_redis_values(config):
    host = config.get("REDIS_HOST", None)
    password = config.get("REDIS_PASSWORD", None)
    port = config.get("REDIS_PORT", None)
    username = config.get("REDIS_USER", None)

    if None in [host, password, port, username]:
        raise ValueError("Missing required Redis configuration values")

    redis_url = f"redis://{username}:{password}@{host}:{port}"
    return redis_url


def get_redis_connection(config, force_new=False):
    """Retrieve Redis connection from the connection pool."""
    global pool
    if pool is None or force_new:
        redis_url = get_redis_values(config)
        pool = ConnectionPool.from_url(redis_url)
    return redis.Redis(connection_pool=pool)


def close_redis_connection(client):
    """Close the Redis connection."""
    client.close()


def configure(**kwargs):
    global app
    config.configure(**kwargs)
    redis_url = get_redis_values(config)
    app = Celery("distributaur", broker=redis_url, backend=redis_url)
    # Disable task events
    app.conf.worker_send_task_events = False
    print("Celery configured.")


env_vars = get_env_vars(".env")
configure(**env_vars)


@app.task(name="call_function_task")
def call_function_task(func_name, args_json):
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
    update_function_status(call_function_task.request.id, "completed")
    return result


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
    return call_function_task.delay(func_name, args_json)


def update_function_status(task_id, status):
    """
    Update the status of a task in Redis.

    Args:
        task_id (str): The ID of the task.
        status (str): The new status of the task.
    """
    redis_client = get_redis_connection(config)
    redis_client.set(f"task_status:{task_id}", status)
