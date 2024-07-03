import os
import time
import argparse
import atexit

from .shared import distributask, example_function

if __name__ == "__main__":
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="Distributask example script")

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
        default="antbaez/distributask-test-worker",
        help="Docker image to use for the worker (default: antbaez/distributask-test-worker)",
    )
    parser.add_argument(
        "--module_name",
        type=str,
        default="distributask.example.worker",
        help="Module name (default: distributask.example.worker)",
    )
    parser.add_argument(
        "--number_of_tasks", type=int, default=10, help="Number of tasks (default: 10)"
    )

    # Parse the arguments
    args = parser.parse_args()

    completed = False

    distributask.register_function(example_function)

    # First, initialize the dataset on Hugging Face
    # This is idempotent, if you run it multiple times it won't delete files that already exist
    distributask.initialize_dataset()

    # Create a file with the current date and time and save it as "datetime.txt"
    with open("datetime.txt", "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S"))

    # Upload this to the repository
    distributask.upload_file("datetime.txt")

    # remove the example file
    os.remove("datetime.txt")

    vast_api_key = distributask.get_env("VAST_API_KEY")
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
    rented_nodes = distributask.rent_nodes(
        args.max_price, args.max_nodes, args.docker_image, args.module_name
    )

    print("Total rented nodes: ", len(rented_nodes))
    print(rented_nodes)

    tasks = []

    repo_id = distributask.get_env("HF_REPO_ID")

    # Submit the tasks to the queue for the worker nodes to execute
    for i in range(args.number_of_tasks):
        job_config = job_configs[i]
        print(f"Task {i}")
        print(job_config)
        print("Task params: ", job_config["task_params"])

        print("Submitting tasks...")

        params = job_config["task_params"]

        # queue up the function for execution on the node
        task = distributask.execute_function(example_function.__name__, params)

        # add the task to the list of tasks
        tasks.append(task)

    def terminate_workers():
        distributask.terminate_nodes(rented_nodes)
        print("Workers terminated.")

    atexit.register(terminate_workers)

    distributask.monitor_tasks(tasks)
