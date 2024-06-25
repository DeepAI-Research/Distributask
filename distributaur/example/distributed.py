import os
import time
import argparse
from tqdm import tqdm
import atexit

from .shared import distributaur, example_function

if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Distributaur example script")

    # Add arguments with default values
    parser.add_argument(
        "--max_price",
        type=float,
        default=0.20,
        help="Max price per node, in dollars (default: 0.20)",
    )
    parser.add_argument(
        "--max_nodes",
        type=int,
        default=1,
        help="Max number of nodes to rent (default: 1)",
    )
    parser.add_argument(
        "--docker_image",
        type=str,
        default="arfx/distributaur-test-worker",
        help="Docker image to use for the worker (default: arfx/distributaur-test-worker)",
    )
    parser.add_argument(
        "--module_name",
        type=str,
        default="distributaur.example.worker",
        help="Module name (default: distributaur.example.worker)",
    )
    parser.add_argument(
        "--number_of_tasks", type=int, default=10, help="Number of tasks (default: 10)"
    )

    # Parse the arguments
    args = parser.parse_args()

    completed = False

    distributaur.register_function(example_function)

    # First, initialize the dataset on Huggingface
    # This is idempotent, if you run it multiple times it won't delete files that already exist
    distributaur.initialize_dataset()

    # Create a file with the current date and time and save it as "datetime.txt"
    with open("datetime.txt", "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S"))

    # Upload this to the repository
    distributaur.upload_file("datetime.txt")

    # remove the example file
    os.remove("datetime.txt")

    vast_api_key = distributaur.get_env("VAST_API_KEY")
    if not vast_api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_configs = []

    # Submit params for the job
    for i in range(args.number_of_tasks):
        job_configs.append(
            {
                "outputs": [f"result_{i}.txt"],
                "task_params": {"index": i, "arg1": 1, "arg2": 2},
            }
        )

    # Rent the nodes and get the node ids
    # This will return a list of node ids that you can use to execute tasks
    print("Renting nodes...")
    rented_nodes = distributaur.rent_nodes(
        args.max_price, args.max_nodes, args.docker_image, args.module_name
    )

    print("Total rented nodes: ", len(rented_nodes))
    print(rented_nodes)

    tasks = []

    repo_id = distributaur.get_env("HF_REPO_ID")

    # Submit the tasks to the queue for the worker nodes to execute
    for i in range(args.number_of_tasks):
        job_config = job_configs[i]
        print(f"Task {i}")
        print(job_config)
        print("Task params: ", job_config["task_params"])

        print("Submitting tasks...")

        params = job_config["task_params"]

        # queue up the function for execution on the node
        task = distributaur.execute_function(example_function.__name__, params)

        # add the task to the list of tasks
        tasks.append(task)

    def tasks_done():
        print("All tasks successfully completed.")

    def terminate_workers():
        distributaur.terminate_nodes(rented_nodes)
        print("Workers terminated.")

    def cleanup_redis():
        patterns = ["celery-task*", "task_status*"]
        redis_connection = distributaur.get_redis_connection()
        for pattern in patterns:
            for key in redis_connection.scan_iter(match=pattern):
                redis_connection.delete(key)

    atexit.register(terminate_workers)
    atexit.register(cleanup_redis)

    first_task_done = False
    # Wait for the tasks to complete
    print("Tasks submitted to queue. Initializing queue...")
    with tqdm(total=len(tasks), unit="task") as pbar:
        while not all(task.ready() for task in tasks):
            current_tasks = sum([task.ready() for task in tasks])
            pbar.update(current_tasks - pbar.n)

            if current_tasks > 0:
                # begin estimation from time of first task
                if not first_task_done:
                    first_task_done = True
                    first_task_start_time = time.time()
                    print("Initialization completed. Tasks started...")

                # calculate and print total elapsed time and estimated time left
                end_time = time.time()
                elapsed_time = end_time - first_task_start_time
                time_per_tasks = elapsed_time / current_tasks
                time_left = time_per_tasks * (len(tasks) - current_tasks)

                pbar.set_postfix(
                    elapsed=f"{elapsed_time:.2f}s", time_left=f"{time_left:.2f}"
                )

    if current_tasks == args.number_of_tasks:
        atexit.register(tasks_done)
