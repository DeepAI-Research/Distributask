import atexit
from subprocess import Popen
import sys

flower_processes = []


def start_monitoring_server(task_name="example_worker") -> None:
    """
    Start Flower monitoring in a separate process.
    The monitoring process will be automatically terminated when the main process exits.
    """
    # get the current python process
    flower_process = Popen(
        [
            "celery",
            "-A",
            {task_name},
            "--broker=redis://default:lQXiTg6afNjUV60JN8QLAYOFYyq7YXZy@redis-17504.c289.us-west-1-2.ec2.redns.redis-cloud.com:17504/0",
            "flower",
        ]
    )

    atexit.register(flower_process.terminate)
    flower_processes.append(flower_process)


def stop_monitoring_server() -> None:
    """
    Stop Flower monitoring by terminating the Flower process.
    """
    for process in flower_processes:
        process.terminate()
    flower_processes.clear()
