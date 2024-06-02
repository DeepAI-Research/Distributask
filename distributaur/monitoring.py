import atexit
from subprocess import Popen

flower_processes = []


def start_monitoring_server(port: int = 5555) -> None:
    """
    Start Flower monitoring in a separate process.
    The monitoring process will be automatically terminated when the main process exits.
    """
    flower_process = Popen(["flower", "--port", str(port)])
    atexit.register(flower_process.terminate)
    flower_processes.append(flower_process)


def stop_monitoring_server() -> None:
    """
    Stop Flower monitoring by terminating the Flower process.
    """
    for process in flower_processes:
        process.terminate()
    flower_processes.clear()
