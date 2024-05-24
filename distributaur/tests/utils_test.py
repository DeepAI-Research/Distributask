# /Users/shawwalters/distributoor/distributaur/tests/utils_test.py

import subprocess
import time
import pytest
from distributaur.config import config
from distributaur.task_runner import configure, execute_function, register_function, registered_functions, update_function_status
from distributaur.utils import get_env_vars, get_redis_connection, get_redis_values, close_redis_connection
from distributaur.config import config

@pytest.fixture
def env_file(tmpdir):
    env_content = """\
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=user
REDIS_PASSWORD=password\
"""
    env_file = tmpdir.join(".env")
    env_file.write(env_content)
    return env_file

env_vars = get_env_vars()
configure(**env_vars)

@pytest.fixture
def redis_client():
    client = get_redis_connection(config)
    yield client
    close_redis_connection(client)

def test_redis_connection(redis_client):
    assert redis_client.ping()
    print("Redis connection test passed")

def test_get_env_vars(env_file):
    env_vars = get_env_vars(env_file)
    assert env_vars == {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_USER": "user",
        "REDIS_PASSWORD": "password",
    }

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
        "--concurrency=1",
        "--heartbeat-interval=1",
    ]
    worker_process = subprocess.Popen(worker_cmd)

    time.sleep(5)

    task_params = {"arg1": 10, "arg2": 20}
    task = execute_function("example_function", task_params)
    result = task.get(timeout=10)

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

