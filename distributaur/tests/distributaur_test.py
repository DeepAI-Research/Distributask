import json
import pytest
import subprocess
import time
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

from huggingface_hub import HfApi

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

from distributaur.distributaur import Distributaur


@pytest.fixture
def mock_task_function():
    """
    Fixture that returns a mock task function.
    """
    return MagicMock()


def test_register_function(mock_task_function):
    """
    Test the register_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    distributaur = Distributaur()
    decorated_task = distributaur.register_function(mock_task_function)

    assert callable(decorated_task)
    assert mock_task_function.__name__ in distributaur.registered_functions
    assert (
        distributaur.registered_functions[mock_task_function.__name__]
        == mock_task_function
    )
    print("Test passed")


@patch("distributaur.distributaur.call_function_task.delay")
def test_execute_function(mock_delay, mock_task_function):
    """
    Test the execute_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    distributaur = Distributaur()
    distributaur.register_function(mock_task_function)

    params = {"arg1": 1, "arg2": 2}
    distributaur.execute_function(mock_task_function.__name__, params)

    mock_delay.assert_called_once_with(mock_task_function.__name__, json.dumps(params))
    print("Test passed")


@patch("distributaur.distributaur.get_redis_connection")
def test_update_function_status(mock_get_redis_connection):
    """
    Test the update_function_status function.
    """
    mock_redis_client = MagicMock()
    mock_get_redis_connection.return_value = mock_redis_client
    distributaur = Distributaur()

    task_id = "task_123"
    status = "SUCCESS"

    distributaur.update_function_status(task_id, status)

    mock_redis_client.set.assert_called_once_with(f"task_status:{task_id}", status)
    print("Test passed")


def test_redis_connection():
    distributaur = Distributaur()
    assert distributaur.redis_client.ping()
    print("Redis connection test passed")


def test_register_function():
    distributaur = Distributaur()

    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    distributaur.register_function(example_function)
    assert "example_function" in distributaur.registered_functions
    assert distributaur.registered_functions["example_function"] == example_function
    print("Task registration test passed")


def test_execute_function():
    distributaur = Distributaur()

    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    distributaur.register_function(example_function)
    task_params = {"arg1": 10, "arg2": 20}
    task = distributaur.execute_function("example_function", task_params)
    assert task.id is not None
    print("Task execution test passed")


def test_worker_task_execution():
    distributaur = Distributaur()

    def example_function(arg1, arg2):
        return f"Result: arg1={arg1}, arg2={arg2}"

    distributaur.register_function(example_function)

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
    task = distributaur.execute_function("example_function", task_params)
    result = task.get(timeout=3)

    assert result == "Result: arg1=10, arg2=20"

    worker_process.terminate()
    worker_process.wait()

    print("Worker task execution test passed")


def test_task_status_update():
    distributaur = Distributaur()
    redis_client = distributaur.get_redis_connection()

    try:
        task_status_keys = redis_client.keys("task_status:*")
        if task_status_keys:
            redis_client.delete(*task_status_keys)

        task_id = "test_task_123"
        status = "COMPLETED"

        distributaur.update_function_status(task_id, status)

        status_from_redis = redis_client.get(f"task_status:{task_id}").decode()
        assert status_from_redis == status

        redis_client.delete(f"task_status:{task_id}")

        print("Task status update test passed")
    finally:
        redis_client.close()


def test_initialize_repo():
    distributaur = Distributaur()

    # Initialize the repository
    distributaur.initialize_dataset()
    hf_token = distributaur.get_env("HF_TOKEN")
    repo_id = distributaur.get_env("HF_REPO_ID")

    # Check if the repository exists
    api = HfApi(token=hf_token)
    repo_info = api.repo_info(repo_id=repo_id, repo_type="dataset")
    assert repo_info["id"] == repo_id

    # Check if the config.json file exists in the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert "config.json" in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_upload_directory():
    distributaur = Distributaur()
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = ["test1.txt", "test2.txt"]
        for file in test_files:
            file_path = os.path.join(temp_dir, file)
            with open(file_path, "w") as f:
                f.write("Test content")

        hf_token = distributaur.get_env("HF_TOKEN")
        repo_id = distributaur.get_env("HF_REPO_ID")
        repo_path = distributaur.get_env("HF_REPO_PATH", "data")

        # Upload the directory to the repository
        distributaur.upload_directory(temp_dir, repo_path)

        # Check if the files exist in the Hugging Face repository
        api = HfApi(token=hf_token)
        repo_files = api.list_repo_files(
            repo_id=repo_id, repo_type="dataset", token=hf_token
        )
        for file in test_files:
            assert os.path.join(repo_path, file) in repo_files

        # Clean up the repository
        api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_delete_file():
    distributaur = Distributaur()

    hf_token = distributaur.get_env("HF_TOKEN")
    repo_id = distributaur.get_env("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # Delete the file from the repository
    distributaur.delete_file(repo_id, test_file)

    # Check if the file is deleted from the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert test_file not in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_file_exists():
    distributaur = Distributaur()

    hf_token = distributaur.get_env("HF_TOKEN")
    repo_id = distributaur.get_env("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # Check if the file exists in the repository
    assert distributaur.file_exists(repo_id, test_file)

    # Check if a non-existent file exists in the repository
    assert not distributaur.file_exists(repo_id, "nonexistent.txt")

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_list_files():
    distributaur = Distributaur()

    hf_token = distributaur.get_env("HF_TOKEN")
    repo_id = distributaur.get_env("HF_REPO_ID")

    # Create test files in the repository
    test_files = ["test1.txt", "test2.txt"]
    api = HfApi(token=hf_token)
    for file in test_files:
        api.upload_file(
            path_or_fileobj=file,
            path_in_repo=file,
            repo_id=repo_id,
            token=hf_token,
            repo_type="dataset",
        )

    # List the files in the repository
    repo_files = distributaur.list_files(repo_id)

    # Check if the test files are present in the repository
    for file in test_files:
        assert file in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


@pytest.fixture(scope="module")
def rented_nodes():
    distributaur = Distributaur()

    max_price = 0.5
    max_nodes = 1
    image = "arfx/distributaur-worker:latest"

    nodes = distributaur.rent_nodes(max_price, max_nodes, image)
    yield nodes

    distributaur.terminate_nodes(nodes)


def test_rent_run_terminate(rented_nodes):
    assert len(rented_nodes) == 1
    time.sleep(3)  # sleep for 3 seconds to simulate runtime
