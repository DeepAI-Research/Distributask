import os
import sys
import time
import pytest
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

from distributaur.core import (
    configure,
    config,
    get_env_vars,
    close_redis_connection,
    get_redis_connection,
)
from distributaur.vast import rent_nodes, terminate_nodes, handle_signal, headers

env_vars = get_env_vars(".env")
configure(**env_vars)


@pytest.fixture(scope="module")
def vast_api_key():
    key = os.getenv("VAST_API_KEY") or env_vars.get("VAST_API_KEY")
    if not key:
        pytest.fail("Vast API key not found.")
    return key


@pytest.fixture(scope="module")
def rented_nodes(vast_api_key):
    headers["Authorization"] = "Bearer " + vast_api_key

    max_price = 0.5
    max_nodes = 1
    image = "arfx/simian-worker:latest"

    nodes = rent_nodes(max_price, max_nodes, image, vast_api_key)
    yield nodes
    terminate_nodes(nodes)


def test_rent_run_terminate(rented_nodes):
    assert len(rented_nodes) == 1
    time.sleep(3)  # sleep for 3 seconds to simulate runtime


def test_handle_signal():
    nodes = [{"instance_id": "instance1"}, {"instance_id": "instance2"}]
    with patch("distributaur.vast.terminate_nodes") as mock_terminate_nodes:
        signal_handler = handle_signal(nodes)
        with pytest.raises(SystemExit) as exc_info:
            signal_handler(None, None)
        assert exc_info.value.code == 0
        mock_terminate_nodes.assert_called_once_with(nodes)


# Add teardown to close Redis connections
def teardown_module(module):
    client = get_redis_connection(config)
    close_redis_connection(client)
