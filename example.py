import os
import sys
import subprocess
import signal
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.utils import get_env_vars
from distributaur.vast import attach_to_existing_job, monitor_job_status, rent_nodes, terminate_nodes, handle_signal
from distributaur.task_runner import execute_function, register_function

def setup_and_run(config):
    # Uncomment if you want to use rent_nodes and handle_signal
    # nodes = rent_nodes(
    #     config["max_price"],
    #     config["max_nodes"],
    #     config["docker_image"],
    #     config["api_key"],
    # )
    # signal.signal(signal.SIGINT, handle_signal(nodes))

    tasks = [
        execute_function(config["task_func"], config["task_params"])
    ]

    for task in tasks:
        print(f"Task {task.id} dispatched.")

    while not all(task.ready() for task in tasks):
        time.sleep(1)
    
    print("All tasks have been completed!")
    # Uncomment if you want to use terminate_nodes
    # terminate_nodes(nodes)

def start_worker():
    worker_cmd = [
        "celery",
        "-A",
        "example_worker",
        "worker",
        "--loglevel=info",
        "--concurrency=1"
    ]
    worker_process = subprocess.Popen(worker_cmd)
    return worker_process

@register_function
def run_workload(arg1, arg2):
    # Perform your rendering task here
    print(f"Rendering object with arg1={arg1} and arg2={arg2}")
    # Simulating rendering time
    time.sleep(5)
    # Return the result or any relevant information
    return f"Rendered object with arg1={arg1} and arg2={arg2}"

register_function(run_workload)

if __name__ == "__main__":
    # Start the worker process
    worker_process = start_worker()

    try:
        env = get_env_vars()
        api_key = env.get("VAST_API_KEY")
        if not api_key:
            raise ValueError("Vast API key not found in environment variables.")

        # Configure your job
        config = {
            "job_id": "example_job",
            "max_price": 0.10,
            "max_nodes": 1,
            "docker_image": "your-docker-image",
            "api_key": api_key,
            "task_func": run_workload.__name__,
            "task_params": {"arg1": 1, "arg2": "a"}
        }

        # Check if the job is already running
        if attach_to_existing_job(config["job_id"]):
            print("Attaching to an existing job...")
            # Monitor job status and handle success/failure conditions
            monitor_job_status(config["job_id"])
        else:
            # Run the job
            setup_and_run(config)
            # Monitor job status and handle success/failure conditions
            monitor_job_status(config["job_id"])

    finally:
        # Terminate the worker process
        worker_process.terminate()
        worker_process.wait()
        print("Worker process terminated.")
