import atexit
import os
import subprocess
import time
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
    number_of_tasks = 3

    # Submit params for the job
    for i in range(number_of_tasks):
        job_configs.append(
            {
                "outputs": [f"result_{i}.txt"],
                "task_params": {"index": i, "arg1": 1, "arg2": 2},
            }
        )

    tasks = []

    repo_id = distributaur.get_env("HF_REPO_ID")

    # Submit the tasks
    # For each task, check if the output files already exist
    for i in range(number_of_tasks):
        job_config = job_configs[i]
        print(f"Task {i}")
        print(job_config)
        print("Task params: ", job_config["task_params"])

        # for each file in job_config["outputs"]
        for output in job_config["outputs"]:
            # check if the file exists in the dataset already
            file_exists = distributaur.file_exists(repo_id, output)

            # if the file exists, ask the user if they want to overwrite it
            if file_exists:
                print("Files already exist. Do you want to overwrite them? (y/n): ")

        print("Submitting tasks...")

        params = job_config["task_params"]

        # queue up the function for execution on the node
        task = distributaur.execute_function(example_function.__name__, params)

        # add the task to the list of tasks
        tasks.append(task)

    # start the worker

    docker_installed = False
    # first, check if docker is installed
    try:
        subprocess.run(["docker", "version"], check=True)
        docker_installed = True
    except Exception as e:
        print("Docker is not installed. Starting worker locally.")
        print(e)

    docker_process = None
    # if docker is installed, start local docker worker
    # if docker is not installed, start local celery worker
    if docker_installed is False:
        print("Docker is not installed. Starting worker locally.")
        celery_worker = subprocess.Popen(
            ["celery", "-A", "distributaur.example.worker", "worker", "--loglevel=info"]
        )

    else:
        build_process = subprocess.Popen(
            [
                "docker",
                "build",
                "-t",
                "distributaur-example-worker",
                ".",
            ]
        )
        build_process.wait()

        docker_process = subprocess.Popen(
            [
                "docker",
                "run",
                "-e",
                f"VAST_API_KEY={vast_api_key}",
                "-e",
                f"REDIS_HOST={distributaur.get_env('REDIS_HOST')}",
                "-e",
                f"REDIS_PORT={distributaur.get_env('REDIS_PORT')}",
                "-e",
                f"REDIS_PASSWORD={distributaur.get_env('REDIS_PASSWORD')}",
                "-e",
                f"REDIS_USER={distributaur.get_env('REDIS_USER')}",
                "-e",
                f"HF_TOKEN={distributaur.get_env('HF_TOKEN')}",
                "-e",
                f"HF_REPO_ID={repo_id}",
                "distributaur-example-worker",
            ]
        )

        def kill_docker():
            print("Killing docker container")
            docker_process.terminate()

        atexit.register(kill_docker)

    def tasks_done():
        print("All tasks successfully completed.")

    def cleanup_redis():
        patterns = ["celery-task*", "task_status*"]
        redis_connection = distributaur.get_redis_connection()
        for pattern in patterns:
            for key in redis_connection.scan_iter(match=pattern):
                redis_connection.delete(key)

    atexit.register(cleanup_redis)

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

                pbar.set_postfix(
                    elapsed=f"{elapsed_time:.2f}s", time_left=f"{time_left:.2f}"
                )

    if current_tasks == number_of_tasks:
        atexit.register(tasks_done)
        celery_worker.terminate()
