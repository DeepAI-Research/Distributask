# example.py

import os
import sys
import subprocess
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.vast import (
    attach_to_existing_job,
    monitor_job_status,
    rent_nodes,
    terminate_nodes,
    handle_signal,
)
from distributaur.core import (
    configure,
    execute_function,
    register_function,
    get_env_vars,
    config,
    call_function_task,
)


def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"


register_function(example_function)


def setup_and_run(config):
    tasks = [execute_function(config["task_func"], config["task_params"])]

    for task in tasks:
        print(f"Task {task.id} dispatched.")

    while not all(task.ready() for task in tasks):
        time.sleep(1)

    print("All tasks have been completed!")


def start_worker():
    worker_cmd = [
        "celery",
        "-A",
        "example_worker",
        "worker",
        "--loglevel=info",
        "--concurrency=1",
    ]
    worker_process = subprocess.Popen(worker_cmd)
    return worker_process


if __name__ == "__main__":
    # Load environment variables from .env file
    env_vars = get_env_vars(".env")
    configure(**env_vars)

    api_key = config.get("VAST_API_KEY")
    if not api_key:
        raise ValueError("Vast API key not found in configuration.")

    # Configure your job
    job_config = {
        "job_id": "example_job",
        "max_price": 0.10,
        "max_nodes": 1,
        "docker_image": "your-docker-image",
        "task_func": "example_function",
        "task_params": {"arg1": 1, "arg2": "a"},
    }

    # Start the worker process
    worker_process = start_worker()

    try:
        # Check if the job is already running
        if attach_to_existing_job(job_config["job_id"]):
            print("Attaching to an existing job...")
            # Monitor job status and handle success/failure conditions
            monitor_job_status(job_config["job_id"])
        else:
            # Run the job
            setup_and_run(job_config)
            # Monitor job status and handle success/failure conditions
            monitor_job_status(job_config["job_id"])

    finally:
        # Terminate the worker process
        worker_process.terminate()
        worker_process.wait()
        print("Worker process terminated.")
