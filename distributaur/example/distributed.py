import os
import time
from distributaur.example.shared import distributaur, example_function
from tqdm import tqdm

from .shared import distributaur, example_function

if __name__ == "__main__":
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

    max_price = 0.10  # max price per node, in dollars
    max_nodes = 3  # max number of nodes to rent
    docker_image = "arfx/distributaur-test-worker"  # docker image to use for the worker
    module_name = "distributaur.example.worker"
    number_of_tasks = 10

    function_name = "example_function"

    # Submit params for the job
    for i in range(number_of_tasks):
        job_configs.append(
            {
                "outputs": [f"result_{i}.txt"],
                "task_params": {"index": i, "arg1": 1, "arg2": 2},
            }
        )

    # Get the job config
    num_nodes_avail = len(distributaur.search_offers(max_price))
    print("Total nodes available: ", num_nodes_avail)

    # Rent the nodes and get the node ids
    # This will return a list of node ids that you can use to execute tasks
    rented_nodes = distributaur.rent_nodes(max_price, max_nodes, docker_image, module_name)

    # Print the rented nodes
    print("Total nodes rented: ", len(rented_nodes))

    distributaur.start_monitoring_server()
    print("Monitoring server started. Visit http://localhost:5555 to monitor the job.")

    tasks = []

    repo_id = distributaur.get_env("HF_REPO_ID")

    print("Submitting tasks...")
    # Submit the tasks
    # For each task, check if the output files already exist
    for i in range(number_of_tasks):
        job_config = job_configs[i]
        # print(f"Task {i} submitted")
        # print(job_config)

        # for each file in job_config["outputs"]
        for output in job_config["outputs"]:
            # check if the file exists in the dataset already
            file_exists = distributaur.file_exists(repo_id, output)

            # if the file exists, ask the user if they want to overwrite it
            # if file_exists:
            #     print("Files already exist. Do you want to overwrite them? (y/n): ")

        params = job_config["task_params"]

        # queue up the function for execution on the node
        task = distributaur.execute_function(function_name, params)

        # add the task to the list of tasks
        tasks.append(task)

    prev_tasks = 0
    first_task_done = False
    queue_start_time = time.time()
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

                pbar.set_postfix(elapsed=f"{elapsed_time:.2f}s", time_left=f"{time_left:.2f}")
            # sleep for a few seconds
            time.sleep(1)

    print("All tasks completed.")
    print("Stopping the nodes in 2 minutes...")
    time.sleep(120)
