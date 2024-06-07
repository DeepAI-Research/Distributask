import os
import time

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

        skip_task = False

        # for each file in job_config["outputs"]
        for output in job_config["outputs"]:
            # check if the file exists in the dataset already
            file_exists = distributaur.file_exists(repo_id, output)

            # if the file exists, ask the user if they want to overwrite it
            if file_exists:
                user_input = input(
                    "Files already exist. Do you want to overwrite them? (y/n): "
                )
                if user_input.lower() == "n":
                    print("Skipping task")
                    skip_task = True
                else:
                    print("Overwriting files")

        if skip_task is False:
            print("Submitting tasks...")

            params = job_config["task_params"]

            # queue up the function for execution on the node
            task = distributaur.execute_function(function_name, params)

            # add the task to the list of tasks
            tasks.append(task)

    # Wait for the tasks to complete
    print("Tasks submitted to queue. Waiting for tasks to complete...")
    while not all(task.ready() for task in tasks):
        print("Tasks completed: " + str([task.ready() for task in tasks]))
        print("Tasks remaining: " + str([task for task in tasks if not task.ready()]))
        # sleep for a few seconds
        time.sleep(1)

    # while True:
    #     user_input = input("Press q to quit monitoring: ")
    #     if user_input.lower() == "q":
    #         print("Stopping monitoring")
    #         stop_monitoring_server()
    #         break
