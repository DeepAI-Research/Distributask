import atexit
from subprocess import Popen
import sys

flower_processes = []


def start_monitoring_server(task_name="example") -> None:
    """
    Start Flower monitoring in a separate process.
    The monitoring process will be automatically terminated when the main process exits.
    """
    # get the current python process
    flower_process = Popen([sys.executable, "-m", "flower", "--app", task_name])
    atexit.register(flower_process.terminate)
    flower_processes.append(flower_process)


def stop_monitoring_server() -> None:
    """
    Stop Flower monitoring by terminating the Flower process.
    """
    for process in flower_processes:
        process.terminate()
    flower_processes.clear()
