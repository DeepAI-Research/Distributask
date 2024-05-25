# Core

The core module contains the core functionality of Distributaur, including the task queue, task execution, and task monitoring.

This guide provides an overview of the core module in the Distributaur package, which handles configuration management, Redis connection, and task execution using Celery.

## Configuration Management

The module uses a `Config` class to manage configuration settings. The `Config` class provides methods to initialize settings from environment variables, update settings, and retrieve values.

### `get_env_vars(path=".env.default")`

This function loads environment variables from a specified file into a dictionary. If the file does not exist, it returns the current environment variables.

### `Config` Class

The `Config` class is responsible for managing configuration settings. It has the following methods:

- `__init__()`: Initializes the `Config` object by loading environment variables as initial settings.
- `configure(**kwargs)`: Updates the configuration settings with provided keyword arguments.
- `get(key, default=None)`: Retrieves a value from the configuration settings, with an optional default if the key is not found.

## Redis Connection

The module provides functions to construct Redis URLs, retrieve or create Redis connections using a connection pool, and close Redis connections.

### `get_redis_values(config)`

This function constructs a Redis URL from the configuration settings. It raises a `ValueError` if any required Redis connection parameter is missing.

### `get_redis_connection(config, force_new=False)`

This function retrieves or creates a new Redis connection using the connection pool. It takes a `Config` object containing Redis connection details and an optional `force_new` parameter to force the creation of a new connection.

### `close_redis_connection(client)`

This function closes a given Redis connection.

## Celery Task Execution

The module uses Celery to execute tasks asynchronously. It provides functions to register functions as tasks, execute tasks, and update task statuses.

### `configure(**kwargs)`

This function configures the application with specified settings and initializes the Celery app.

### `call_function_task(func_name, args_json)`

This is a Celery task that executes a registered function with provided JSON arguments. It raises a `ValueError` if the function name is not registered.

### `register_function(func)`

This is a decorator used to register a function so that it can be invoked as a task.

### `execute_function(func_name, args)`

This function executes a registered function as a Celery task with provided arguments. It returns an `AsyncResult` object representing the asynchronous result of the task.

### `update_function_status(task_id, status)`

This function updates the status of a function task in Redis.

## Job Monitoring

The module provides functions to monitor the status of jobs and their associated tasks.

### `check_job_status(job_id)`

This function checks the status counts of tasks for a job in Redis. It returns a dictionary with the counts of each status type for the job's tasks.

### `monitor_job_status(job_id)`

This function continuously monitors the status of a job until there are no more active or pending tasks.

### `attach_to_existing_job(job_id)`

This function checks if a job has any active or pending tasks and determines if it's possible to attach to it. It returns `True` if the job has active or pending tasks, otherwise `False`.

This guide provides an overview of the core module and explains the purpose and usage of each function and class. It can be used as a reference when working with the Distributaur package.

::: distributaur.core
    :docstring:
    :members:
    :undoc-members:
    :show-inheritance: