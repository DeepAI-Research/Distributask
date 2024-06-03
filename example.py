import os
import sys
import subprocess
import time


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.monitoring import start_monitoring_server
from distributaur.distributaur import Distributaur


def example_function(arg1, arg2):
    return f"Result: {arg1 + arg2}"


distributaur = Distributaur()
distributaur.register_function(example_function)

if __name__ == "__main__":
    api_key = distributaur.get_env("VAST_API_KEY")
    if not api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_config = {
        "max_price": 0.10,
        "max_nodes": 10,
        "docker_image": "your-docker-image",
        "task_func": "example_function",
        "task_params": {"arg1": 1, "arg2": 2},
    }

    worker_cmd = [
        "celery",
        "-A",
        "example_worker",
        "worker",
        "--loglevel=info",
        "--concurrency=1",
    ]
    worker_process = subprocess.Popen(worker_cmd)

    print("Worker process started.")

    start_monitoring_server()
    print("Monitoring server started. Visit http://localhost:5555 to monitor the job.")

    try:
        print("Submitting tasks...")
        tasks = [
            distributaur.execute_function(
                job_config["task_func"], job_config["task_params"]
            )
        ]

        print("Tasks submitted to queue. Waiting for tasks to complete...")

        while not all(task.ready() for task in tasks):
            print("Tasks completed: " + str([task.ready() for task in tasks]))
            print(
                "Tasks remaining: " + str([task for task in tasks if not task.ready()])
            )
            # sleep for a few seconds
            time.sleep(5)
            pass

    finally:
        worker_process.terminate()
        worker_process.wait()
        print("Worker process terminated.")
