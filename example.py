import os
import sys
import subprocess
import time


sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.monitoring import start_monitoring_server, stop_monitoring_server
from distributaur.distributaur import Distributaur

def example_function(index, arg1, arg2):
    # Create expected outputs
    result = arg1 + arg2
    
    # save the result to a file
    with open(f"result_{index}.txt", "w") as f:
        f.write(str(result))
    
    return f"Result: {result}"

distributaur = Distributaur()
distributaur.register_function(example_function)

if __name__ == "__main__":
    # Create a new repository if it doesn't exist
    
    # Then, create a file with the current date and time and save it as "datetime.txt"
    
    # Upload this to the repository
    
    
    api_key = distributaur.get_env("VAST_API_KEY")
    if not api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_config = {
        "index": "0",
        "max_price": 0.10,
        "max_nodes": 10,
        "docker_image": "your-docker-image",
        "task_func": "example_function",
        "outputs": ["result_*.txt"],
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
    worker_process = subprocess.Popen(worker_cmd)

    print("Worker process started.")

    start_monitoring_server()
    print("Monitoring server started. Visit http://localhost:5555 to monitor the job.")

    # Check if the 'outputs' already exist in the current huggingface repo and ask user if they want to overwrite
    # If they want to overwrite, delete the existing files
    # If they don't want to overwrite, skip the task
    
    skip_task = False
    # for each file in job_config["outputs"]
    for output in job_config["outputs"]:
        # replace * with the index of the task
        output = output.replace("*", job_config["index"])
        file_exists = distributaur.file_exists(output)
    
        if file_exists:
            user_input = input("Files already exist. Do you want to overwrite them? (y/n): ")
            if user_input.lower() == "n":
                print("Skipping task")
                skip_task = True
            else:
                print("Overwriting files")
                distributaur.delete_file(output)

    if skip_task is False:        
        print("Submitting tasks...")
        tasks = [
            distributaur.execute_function(
                job_config["index"], job_config["task_func"], job_config["task_params"]
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

            user_input = input("Press q to quit monitoring: ")
            if user_input.lower() == "q":
                print("Stopping monitoring")
                stop_monitoring_server()

            pass

    worker_process.terminate()
    worker_process.wait()
    print("Worker process terminated.")
