import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.core import (
    configure,
    execute_function,
    register_function,
    get_env_vars,
    config,
    attach_to_existing_job,
    monitor_job_status,
)


# Some function that does something
def example_function(arg1, arg2):
    return f"Result: {arg1 + arg2}"


register_function(example_function)


# This is an example, so we're starting to worker right here
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
    env_vars = get_env_vars(".env")
    configure(**env_vars)

    api_key = config.get("VAST_API_KEY")
    if not api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_config = {
        "job_id": "example_job",
        "max_price": 0.15,
        "max_nodes": 10,
        "docker_image": "your-docker-image",
        "task_func": "example_function",
        "task_params": {"arg1": 1, "arg2": 2},
    }

    worker_process = start_worker()

    try:
        if attach_to_existing_job(job_config["job_id"]):
            print("Attaching to an existing job...")
            monitor_job_status(job_config["job_id"])
        else:
            tasks = [execute_function(config["task_func"], config["task_params"])]
            monitor_job_status(job_config["job_id"])

    finally:
        worker_process.terminate()
        worker_process.wait()
        print("Worker process terminated.")
