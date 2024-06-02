import json
import pytest
import subprocess
import time
import os
import tempfile
from unittest.mock import MagicMock, patch

from distributaur.core import (
    execute_function,
    get_env_vars,
    register_function,
    registered_functions,
    close_redis_connection,
    get_redis_connection,
    config,
    registered_functions,
    update_function_status,
)


@pytest.fixture
def mock_task_function():
    """
    Fixture that returns a mock task function.
    """
    return MagicMock()


def test_get_env_vars():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_file.write("KEY1=value1\nKEY2=value2")
        temp_file.close()

        env_vars = get_env_vars(temp_file.name)
        assert env_vars == {"KEY1": "value1", "KEY2": "value2"}

        os.unlink(temp_file.name)


def test_register_function(mock_task_function):
    """
    Test the register_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    decorated_task = register_function(mock_task_function)

    assert callable(decorated_task)
    assert mock_task_function.__name__ in registered_functions
    assert registered_functions[mock_task_function.__name__] == mock_task_function
    print("Test passed")


@patch("distributaur.core.call_function_task.delay")
def test_execute_function(mock_delay, mock_task_function):
    """
    Test the execute_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    register_function(mock_task_function)

    params = {"arg1": 1, "arg2": 2}
    execute_function(mock_task_function.__name__, params)

    mock_delay.assert_called_once_with(mock_task_function.__name__, json.dumps(params))
    print("Test passed")


@patch("distributaur.core.get_redis_connection")
def test_update_function_status(mock_get_redis_connection):
    """
    Test the update_function_status function.
    """
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client

    task_id = "task_123"
    status = "SUCCESS"

    update_function_status(task_id, status)

    mock_redis_client.set.assert_called_once_with(f"task_status:{task_id}", status)
    print("Test passed")


@pytest.fixture
def redis_client():
    client = get_redis_connection(config, force_new=True)
    yield client
    close_redis_connection(client)


def test_redis_connection(redis_client):
    assert redis_client.ping()
    print("Redis connection test passed")


def test_get_redis_connection(redis_client):
    assert redis_client.ping()
    print("Redis connection test passed")


def test_register_function():
    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    register_function(example_function)
    assert "example_function" in registered_functions
    assert registered_functions["example_function"] == example_function
    print("Task registration test passed")


def test_execute_function():
    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    register_function(example_function)
    task_params = {"arg1": 10, "arg2": 20}
    task = execute_function("example_function", task_params)
    assert task.id is not None
    print("Task execution test passed")


def test_worker_task_execution():
    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    register_function(example_function)

    worker_cmd = [
        "celery",
        "-A",
        "distributaur.tests.test_worker",
        "worker",
        "--loglevel=info",
    ]
    print("worker_cmd")
    print(worker_cmd)
    worker_process = subprocess.Popen(worker_cmd)

    time.sleep(5)

    task_params = {"arg1": 10, "arg2": 20}
    task = execute_function("example_function", task_params)
    result = task.get(timeout=3)

    assert result == "Result: arg1=10, arg2=20"

    worker_process.terminate()
    worker_process.wait()

    print("Worker task execution test passed")


def test_task_status_update():
    redis_client = get_redis_connection(config)

    try:
        task_status_keys = redis_client.keys("task_status:*")
        if task_status_keys:
            redis_client.delete(*task_status_keys)

        task_id = "test_task_123"
        status = "COMPLETED"

        update_function_status(task_id, status)

        status_from_redis = redis_client.get(f"task_status:{task_id}").decode()
        assert status_from_redis == status

        redis_client.delete(f"task_status:{task_id}")

        print("Task status update test passed")
    finally:
        close_redis_connection(redis_client)


def teardown_module():
    client = get_redis_connection(config)
    close_redis_connection(client)
