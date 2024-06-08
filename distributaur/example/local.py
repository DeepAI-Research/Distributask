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
    number_of_tasks = 5

    # Submit params for the job
    for i in range(number_of_tasks):
        job_configs.append(
            {
                "outputs": [f"result_{i}.txt"],
                "task_params": {"index": i, "arg1": 1, "arg2": 2},
            }
        )

    distributaur.start_monitoring_server()
    print("Monitoring server started. Visit http://localhost:5555 to monitor the job.")

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
    # first, try starting the docker container
    # if that errors, start the worker locally

    # TODO:

    docker_installed = False

    # first, check if docker is installed
    try:
        subprocess.run(["docker", "--version"], check=True)
        docker_installed = True
    except Exception as e:
        print("Docker is not installed. Starting worker locally.")
        print(e)

    docker_process = None

    if docker_installed is False:
        print("Docker is not installed. Starting worker locally.")
        subprocess.Popen(
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

    # Wait for the tasks to complete
    print("Tasks submitted to queue. Waiting for tasks to complete...")
    with tqdm(total=len(tasks), unit="task") as pbar:
        while not all(task.ready() for task in tasks):
            completed_tasks = sum([task.ready() for task in tasks])
            pbar.update(completed_tasks - pbar.n)
            # sleep for a few seconds
            time.sleep(1)

    # while True:
    #     user_input = input("Press q to quit monitoring: ")
    #     if user_input.lower() == "q":
    #         print("Stopping monitoring")
    #         stop_monitoring_server()
    #         break
