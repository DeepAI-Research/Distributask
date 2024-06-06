import os
import sys
import subprocess
import time
import keyboard

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.monitoring import start_monitoring_server, stop_monitoring_server
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
        "max_nodes": 1,
        "docker_image": "arfx/distributaur-test-worker",
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

    # worker_process = subprocess.Popen(worker_cmd)
    # print("Worker process started.")

    num_nodes_avail = len(distributaur.search_offers(job_config["max_price"]))
    print("TOTAL NODES AVAILABLE: ", num_nodes_avail)

    rented_nodes = distributaur.rent_nodes(
        job_config["max_price"], job_config["max_nodes"], job_config["docker_image"]
    )
    print("TOTAL RENTED NODES: ", len(rented_nodes))

    print(rented_nodes)

    for node in rented_nodes:
        distributaur.execute_command(
            node, worker_cmd
        )  # give the worker_cmd to the GPUs

    start_monitoring_server()
    print("Monitoring server started. Visit http://localhost:5555 to monitor the job.")

    # while True:
    #     logs = distributaur.get_logs(rented_nodes[0])
    #     print("LOGS: ", logs["instances"]["actual_status"])

    #     time.sleep(1)

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

            # user_input = input("Press q to quit monitoring: ")
            # if user_input.lower() == "q":
            #     print("Stopping monitoring")
            #     stop_monitoring_server()
            #     break
            pass

    finally:
        # worker_process.terminate()
        # worker_process.wait()
        distributaur.terminate_nodes(rented_nodes)

        print("Worker process terminated.")
