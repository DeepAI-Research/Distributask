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

    args = parser.parse_args()

    completed = False

    # Register function to distributask object
    distributask.register_function(example_function)

    # Initialize the dataset on Hugging Face
    distributask.initialize_dataset()

    # Create a file with the current date and time and save it as "datetime.txt"
    with open("datetime.txt", "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S"))

    # Upload file to the repository
    distributask.upload_file("datetime.txt")

    # Remove the example file from local
    os.remove("datetime.txt")

    vast_api_key = distributask.get_env("VAST_API_KEY")
    if not vast_api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_configs = []

    # Compile parameters for tasks
    for i in range(args.number_of_tasks):
        job_configs.append(
            {
                "outputs": [f"result_{i}.txt"],
                "task_params": {"index": i, "arg1": 1, "arg2": 2},
            }
        )

    # Rent Vast.ai nodes and get list of node ids
    print("Renting nodes...")
    rented_nodes = distributask.rent_nodes(
        args.max_price, args.max_nodes, args.docker_image, args.module_name
    )

    print("Total rented nodes: ", len(rented_nodes))

    tasks = []

    # Submit the tasks to the queue for the Vast.ai worker nodes to execute
    for i in range(args.number_of_tasks):
        job_config = job_configs[i]
        print(f"Task {i}")
        print(job_config)
        print("Task params: ", job_config["task_params"])

        params = job_config["task_params"]

        # Each task executes the function "example_function", defined in shared.py
        task = distributask.execute_function(example_function.__name__, params)

        # Add the task to the list of tasks
        tasks.append(task)

    def terminate_workers():
        distributask.terminate_nodes(rented_nodes)
        print("Workers terminated.")

    # Terminate Vast.ai nodes on exit of script
    atexit.register(terminate_workers)

    # Monitor the status of the tasks with tqdm
    distributask.monitor_tasks(tasks)
