import json
import pytest
import time
import os
import tempfile
from unittest.mock import MagicMock, patch

from huggingface_hub import HfApi

from ..distributask import create_from_config
from .worker import example_test_function


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
    distributask = create_from_config()
    decorated_task = distributask.register_function(mock_task_function)

    assert callable(decorated_task)
    assert mock_task_function.__name__ in distributask.registered_functions
    assert (
        distributask.registered_functions[mock_task_function.__name__]
        == mock_task_function
    )
    print("Test passed")


@patch("distributask.distributask.call_function_task.delay")
def test_execute_function(mock_delay, mock_task_function):
    """
    Test the execute_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    distributask = create_from_config()
    distributask.register_function(mock_task_function)

    params = {"arg1": 1, "arg2": 2}
    distributask.execute_function(mock_task_function.__name__, params)

    mock_delay.assert_called_once_with(mock_task_function.__name__, json.dumps(params))
    print("Test passed")


def test_register_function():
    distributask = create_from_config()

    distributask.register_function(example_test_function)
    assert "example_test_function" in distributask.registered_functions
    assert (
        distributask.registered_functions["example_test_function"]
        == example_test_function
    )
    print("Task registration test passed")


def test_execute_function():
    distributask = create_from_config()

    distributask.register_function(example_test_function)
    task_params = {"arg1": 10, "arg2": 20}
    task = distributask.execute_function("example_test_function", task_params)
    assert task.id is not None
    print("Task execution test passed")


# def test_worker_task_execution():
#     distributask = create_from_config()

#     distributask.register_function(example_test_function)

#     worker_cmd = [
#         "celery",
#         "-A",
#         "distributask.tests.worker",
#         "worker",
#         "--loglevel=info",
#     ]
#     print("worker_cmd")
#     print(worker_cmd)
#     worker_process = subprocess.Popen(worker_cmd)

#     time.sleep(2)

#     task_params = {"arg1": 10, "arg2": 20}
#     print("executing task")
#     task = distributask.execute_function("example_test_function", task_params)
#     result = task.get(timeout=30)

#     assert result == "+arg2=30"

#     worker_process.terminate()
#     worker_process.wait()

#     print("Worker task execution test passed")


def test_task_status_update():
    distributask = create_from_config()
    redis_client = distributask.get_redis_connection()

    task_status_keys = redis_client.keys("task_status:*")
    if task_status_keys:
        redis_client.delete(*task_status_keys)

    task_id = "test_task_123"
    status = "COMPLETED"

    distributask.update_function_status(task_id, status)

    status_from_redis = redis_client.get(f"task_status:{task_id}").decode()
    assert status_from_redis == status

    redis_client.delete(f"task_status:{task_id}")

    print("Task status update test passed")


def test_initialize_repo():
    distributask = create_from_config()

    # Initialize the repository
    distributask.initialize_dataset()
    hf_token = distributask.get_env("HF_TOKEN")
    repo_id = distributask.get_env("HF_REPO_ID")

    print("repo_id")
    print(repo_id)

    print("hf_token")
    print(hf_token)

    # Check if the repository exists
    api = HfApi(token=hf_token)
    repo_info = api.repo_info(repo_id=repo_id, repo_type="dataset", timeout=30)
    assert repo_info.id == repo_id

    # Check if the config.json file exists in the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert "config.json" in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_upload_directory():
    distributask = create_from_config()
    distributask.initialize_dataset()
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = ["test1.txt", "test2.txt"]
        for file in test_files:
            file_path = os.path.join(temp_dir, file)
            with open(file_path, "w") as f:
                f.write("Test content")

        hf_token = distributask.get_env("HF_TOKEN")
        repo_id = distributask.get_env("HF_REPO_ID")
        repo_path = distributask.get_env("HF_REPO_PATH", "data")

        # Upload the directory to the repository
        distributask.upload_directory(temp_dir)

        # Check if the files exist in the Hugging Face repository
        api = HfApi(token=hf_token)
        repo_files = api.list_repo_files(
            repo_id=repo_id, repo_type="dataset", token=hf_token
        )
        for file in test_files:
            print(file)
            assert file in repo_files

        for file in test_files:
            os.remove(os.path.join(temp_dir, file))

        # Clean up the repository
        api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_delete_file():
    distributask = create_from_config()
    distributask.initialize_dataset()
    hf_token = distributask.get_env("HF_TOKEN")
    repo_id = distributask.get_env("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # delete the file on disk
    os.remove(test_file)

    # Delete the file from the repository
    distributask.delete_file(repo_id, test_file)

    # Check if the file is deleted from the repository
    repo_files = api.list_repo_files(
        repo_id=repo_id, repo_type="dataset", token=hf_token
    )
    assert test_file not in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_file_exists():
    distributask = create_from_config()
    distributask.initialize_dataset()
    hf_token = distributask.get_env("HF_TOKEN")
    repo_id = distributask.get_env("HF_REPO_ID")

    # Create a test file in the repository
    test_file = "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    api = HfApi(token=hf_token)
    api.upload_file(
        path_or_fileobj=test_file,
        path_in_repo=test_file,
        repo_id=repo_id,
        token=hf_token,
        repo_type="dataset",
    )

    # delete the file on disk
    os.remove(test_file)

    # Check if the file exists in the repository
    assert distributask.file_exists(repo_id, test_file)

    # Check if a non-existent file exists in the repository
    assert not distributask.file_exists(repo_id, "nonexistent.txt")

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


def test_list_files():
    distributask = create_from_config()
    distributask.initialize_dataset()
    hf_token = distributask.get_env("HF_TOKEN")
    repo_id = distributask.get_env("HF_REPO_ID")

    # Create test files in the repository
    test_files = ["test1.txt", "test2.txt"]
    # for each test_file, write the file
    for file in test_files:
        with open(file, "w") as f:
            f.write("Test content")
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
    repo_files = distributask.list_files(repo_id)

    for file in test_files:
        os.remove(file)

    # Check if the test files are present in the repository
    for file in test_files:
        assert file in repo_files

    # Clean up the repository
    api.delete_repo(repo_id=repo_id, repo_type="dataset", token=hf_token)


@pytest.fixture(scope="module")
def rented_nodes():
    distributask = create_from_config()

    max_price = 0.5
    max_nodes = 1
    image = "antbaez/distributask-worker:latest"
    module_name = "distributask.example.worker"

    nodes = distributask.rent_nodes(max_price, max_nodes, image, module_name)
    yield nodes

    distributask.terminate_nodes(nodes)


def test_rent_run_terminate(rented_nodes):
    assert len(rented_nodes) == 1
    time.sleep(3)  # sleep for 3 seconds to simulate runtime


def test_get_redis_url():
    distributask = create_from_config()
    redis_url = distributask.get_redis_url()

    assert redis_url.startswith("redis://")
    assert distributask.settings["REDIS_USER"] in redis_url
    assert distributask.settings["REDIS_PASSWORD"] in redis_url
    assert distributask.settings["REDIS_HOST"] in redis_url
    assert str(distributask.settings["REDIS_PORT"]) in redis_url


def test_get_redis_connection_force_new():
    distributask = create_from_config()
    redis_client1 = distributask.get_redis_connection()
    redis_client2 = distributask.get_redis_connection(force_new=True)

    assert redis_client1 is not redis_client2


def test_get_redis_connection_force_new():
    distributask = create_from_config()
    redis_client1 = distributask.get_redis_connection()
    redis_client2 = distributask.get_redis_connection(force_new=True)

    assert redis_client1 is not redis_client2


def test_get_env_with_default():
    distributask = create_from_config()
    default_value = "default"
    value = distributask.get_env("NON_EXISTENT_KEY", default_value)

    assert value == default_value


@patch("requests.get")
def test_search_offers(mock_get):
    distributask = create_from_config()
    max_price = 1.0

    mock_response = MagicMock()
    mock_response.json.return_value = {"offers": [{"id": "offer1"}, {"id": "offer2"}]}
    mock_get.return_value = mock_response

    offers = distributask.search_offers(max_price)

    assert len(offers) == 2
    assert offers[0]["id"] == "offer1"
    assert offers[1]["id"] == "offer2"


@patch("requests.put")
def test_create_instance(mock_put):
    distributask = create_from_config()
    offer_id = "offer1"
    image = "test_image"
    module_name = "distributask.example.worker"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"new_contract": "instance1"}
    mock_put.return_value = mock_response

    instance = distributask.create_instance(offer_id, image, module_name)

    assert instance["new_contract"] == "instance1"


from io import StringIO
import subprocess
import re


def test_local_example_run():
    # Capture the stdout and stderr during the execution
    with patch("sys.stdout", new=StringIO()) as fake_out, patch(
        "sys.stderr", new=StringIO()
    ) as fake_err:

        # Start a new process to run the local example
        process = subprocess.Popen(["python", "-m", "distributask.example.local"])
        # if process hasn't ended in 3min, test is failed
        process.wait(timeout=180)

        # Get the captured output from stdout
        # output = fake_out.getvalue()
        # print(output)

        # Assert that no errors are captured in stderr
        assert fake_err.getvalue() == ""

        try:
            stop_command = "docker stop $(docker ps -q)"
            subprocess.run(stop_command, shell=True, check=True)
            print("All containers stopped successfully")
        except:
            pass


def test_distributed_example_run():
    # Capture the stdout and stderr during the execution
    with patch("sys.stdout", new=StringIO()) as fake_out, patch(
        "sys.stderr", new=StringIO()
    ) as fake_err:

        # Start a new process to run the local example
        process = subprocess.Popen(
            ["python", "-m", "distributask.example.distributed", "--number_of_tasks=3"]
        )
        # if process hasn't ended in 2min, test is failed
        process.wait(timeout=120)

        # Get the captured output from stdout
        # output = fake_out.getvalue()
        # print(output)

        # Assert that no errors are captured in stderr
        assert fake_err.getvalue() == ""
