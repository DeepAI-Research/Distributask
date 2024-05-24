import json
import pytest
from unittest.mock import MagicMock, patch

from distributaur.task_runner import execute_function, register_function, update_function_status, registered_functions
from distributaur.utils import close_redis_connection, get_redis_connection
from distributaur.config import config

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
    decorated_task = register_function(mock_task_function)

    assert callable(decorated_task)
    assert mock_task_function.__name__ in registered_functions
    assert registered_functions[mock_task_function.__name__] == mock_task_function
    print("Test passed")

@patch("distributaur.task_runner.call_function.delay")
def test_execute_function(mock_delay, mock_task_function):
    """
    Test the execute_function function.
    """
    mock_task_function.__name__ = "mock_task"  # Set the __name__ attribute
    register_function(mock_task_function)

    params = {'arg1': 1, 'arg2': 2}
    execute_function(mock_task_function.__name__, params)

    mock_delay.assert_called_once_with(mock_task_function.__name__, json.dumps(params))
    print("Test passed")

@patch("distributaur.task_runner.get_redis_connection")
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

# Add teardown to close Redis connections
def teardown_module(module):
    client = get_redis_connection(config)
    close_redis_connection(client)
