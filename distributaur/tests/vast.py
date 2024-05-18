import os
import sys
import time
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
simian_path = os.path.join(current_dir, "../")
sys.path.append(simian_path)

from distributaur.vast import rent_nodes, terminate_nodes, headers
from distributaur.utils import get_env_vars


@pytest.fixture(scope="module")
def vast_api_key():
    env_vars = get_env_vars()
    key = os.getenv("VAST_API_KEY") or env_vars.get("VAST_API_KEY")
    if not key:
        pytest.fail("Vast API key not found.")
    return key


@pytest.fixture(scope="module")
def rented_nodes(vast_api_key):
    headers["Authorization"] = "Bearer " + vast_api_key

    max_price = 0.5
    max_nodes = 1
    image = "arfx/distributaur-example-worker-worker:latest"

    nodes = rent_nodes(max_price, max_nodes, image, vast_api_key)
    yield nodes
    terminate_nodes(nodes)


def test_rent_run_terminate(rented_nodes):
    assert len(rented_nodes) == 1
    time.sleep(3)  # sleep for 3 seconds to simulate runtime
