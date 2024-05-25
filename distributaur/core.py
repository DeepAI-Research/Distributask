import time
from celery import Celery
import os
import sys
import json
import redis
from redis import ConnectionPool

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

app: Celery = None
registered_functions: dict = {}
pool: ConnectionPool = None


def get_env_vars(path: str = ".env.default") -> dict:
    """
    Load environment variables from a specified file into a dictionary.
    If the file does not exist, this function simply returns the current environment variables.

    Args:
        path (str): The path to the environment variable file, with a default of ".env.default".

    Returns:
        dict: A dictionary containing all the environment variables, updated with those from the file if it exists.
    """
    env_vars = os.environ.copy()
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                env_vars[key] = value
    return env_vars


class Config:
    """
    Configuration management class that stores settings and provides methods to update and retrieve these settings.
    """

    def __init__(self) -> None:
        """
        Initialize the Config object by loading environment variables as initial settings.
        """
        self.settings = {}
        self.settings.update(get_env_vars())

    def configure(self, **kwargs) -> None:
        """
        Update the configuration settings with provided keyword arguments.

        Args:
            **kwargs: Key-value pairs to update in the settings.
        """
        self.settings.update(kwargs)

    def get(self, key: str, default: any = None) -> any:
        """
        Retrieve a value from the configuration settings, with an optional default if the key is not found.

        Args:
            key (str): The key to look for in the settings.
            default (any, optional): The default value to return if the key is not found.

        Returns:
            any: The value from the settings if the key exists, otherwise the default value.
        """
        return self.settings.get(key, default)


config = Config()


def get_redis_values(config: Config) -> str:
    """
    Construct a Redis URL from the configuration settings.

    Args:
        config (Config): The configuration object containing Redis connection details.

    Returns:
        str: A Redis URL string built from the configuration settings.

    Raises:
        ValueError: If any required Redis connection parameter is missing.
    """
    host = config.get("REDIS_HOST", None)
    password = config.get("REDIS_PASSWORD", None)
    port = config.get("REDIS_PORT", None)
    username = config.get("REDIS_USER", None)

    if None in [host, password, port, username]:
        raise ValueError("Missing required Redis configuration values")

    redis_url = f"redis://{username}:{password}@{host}:{port}"
    return redis_url


def get_redis_connection(config: Config, force_new: bool = False) -> redis.Redis:
    """
    Retrieve or create a new Redis connection using the connection pool.

    Args:
        config (Config): The configuration object containing Redis connection details.
        force_new (bool): Force the creation of a new connection if set to True.

    Returns:
        Redis: A Redis connection object.
    """
    global pool
    if pool is None or force_new:
        redis_url = get_redis_values(config)
        pool = ConnectionPool.from_url(redis_url)
    return redis.Redis(connection_pool=pool)


def configure(**kwargs) -> None:
    """
    Configure the application with specified settings and initialize the Celery app.

    Args:
        **kwargs: Configuration settings to apply.
    """
    global app
    config.configure(**kwargs)
    redis_url = get_redis_values(config)
    app = Celery("distributaur", broker=redis_url, backend=redis_url)
    # Disable task events
    app.conf.worker_send_task_events = False


env_vars = get_env_vars(".env")
configure(**env_vars)


redis_client = get_redis_connection(config, force_new=True)


def close_redis_connection(client: redis.Redis) -> None:
    """
    Close a given Redis connection.

    Args:
        client (Redis): The Redis client to close.
    """
    client.close()


@app.task(name="call_function_task")
def call_function_task(func_name: str, args_json: str) -> any:
    """
    Celery task to execute a registered function with provided JSON arguments.

    Args:
        func_name (str): The name of the registered function to execute.
        args_json (str): JSON string representation of the arguments for the function.

    Returns:
        any: The result of the function execution.

    Raises:
        ValueError: If the function name is not registered.
    """
    if func_name not in registered_functions:
        raise ValueError(f"Function '{func_name}' is not registered.")

    func = registered_functions[func_name]
    args = json.loads(args_json)
    result = func(**args)
    update_function_status(call_function_task.request.id, "completed")
    return result


def register_function(func: callable) -> callable:
    """
    Decorator to register a function so that it can be invoked as a task.

    Args:
        func (callable): The function to register.

    Returns:
        callable: The original function, now registered as a callable task.
    """
    registered_functions[func.__name__] = func
    return func


def execute_function(func_name: str, args: dict) -> Celery.AsyncResult:
    """
    Execute a registered function as a Celery task with provided arguments.

    Args:
        func_name (str): The name of the function to execute.
        args (dict): Arguments to pass to the function.

    Returns:
        AsyncResult: An object representing the asynchronous result of the task.
    """
    args_json = json.dumps(args)
    return call_function_task.delay(func_name, args_json)


def update_function_status(task_id: str, status: str) -> None:
    """
    Update the status of a function task in Redis.

    Args:
        task_id (str): The ID of the task.
        status (str): The new status to set.
    """
    redis_client = get_redis_connection(config)
    redis_client.set(f"task_status:{task_id}", status)


def check_job_status(job_id: str) -> dict:
    """
    Check the status counts of tasks for a job in Redis.

    Args:
        job_id (str): The ID of the job whose tasks to check.

    Returns:
        dict: A dictionary with the counts of each status type for the job's tasks.
    """
    task_keys = redis_client.keys(f"celery-task-meta-*")

    status_counts = {"PENDING": 0, "STARTED": 0, "RETRY": 0, "FAILURE": 0, "SUCCESS": 0}

    for key in task_keys:
        value = redis_client.get(key)
        if value:
            task_meta = json.loads(value)
            status = task_meta.get("status")
            if status in status_counts:
                status_counts[status] += 1
            else:
                print(f"Unknown status '{status}' for task key '{key.decode('utf-8')}'")

    return status_counts


def monitor_job_status(job_id: str) -> None:
    """
    Continuously monitor the status of a job until there are no more active or pending tasks.

    Args:
        job_id (str): The ID of the job to monitor.
    """
    while True:
        status_counts = check_job_status(job_id)
        if status_counts["STARTED"] == 0 and status_counts["PENDING"] == 0:
            break
        time.sleep(30)  # Polling interval, adjust as needed


def attach_to_existing_job(job_id: str) -> bool:
    """
    Check if a job has any active or pending tasks and determine if it's possible to attach to it.

    Args:
        job_id (str): The ID of the job to check.

    Returns:
        bool: True if the job has active or pending tasks, otherwise False.
    """
    status_counts = check_job_status(job_id)
    return status_counts["STARTED"] > 0 or status_counts["PENDING"] > 0
