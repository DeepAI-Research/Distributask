import atexit
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.monitoring import start_monitoring_server, stop_monitoring_server
from distributaur.distributaur import Distributaur

distributaur = Distributaur()

completed = False

def handle_exit(rented_nodes):
    global completed
    if not completed:
        print("Terminating nodes...")
        distributaur.terminate_nodes(rented_nodes)
        print("Worker process terminated.")
        stop_monitoring_server()
        print("Monitoring server stopped.")
        completed = True

# This is the function that will be executed on the nodes
# You can make your own function and pass in whatever arguments you want
def example_function(index, arg1, arg2):
    
    # As an ext
    result = arg1 + arg2
    
    # sleep for 5 seconds to simulate a long running task
    time.sleep(5)
    
    # save the result to a file
    with open(f"result_{index}.txt", "w") as f:
        f.write(f"{str(arg1)} plus {str(arg2)} is {str(result)}")
    
    # write the file to huggingface
    distributaur.upload_file(f"result_{index}.txt")
    
    # now destroy the file
    os.remove(f"result_{index}.txt")
    
    # return the result - you can get this value from the task object
    return f"Task {index} completed. Result ({str(arg1)} + {str(arg2)}): {str(result)}"


# Register the function with Distributaur so that it knows what to execute
distributaur.register_function(example_function)

if __name__ == "__main__":
    # First, initialize the dataset on Huggingface
    # This is idempotent, if you run it multiple times it won't delete files that already exist
    distributaur.initialize_dataset()
    
    # Create a file with the current date and time and save it as "datetime.txt"
    with open("datetime.txt", "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Upload this to the repository
    distributaur.upload_file("datetime.txt")
    
    
    vast_api_key = distributaur.get_env("VAST_API_KEY")
    if not vast_api_key:
        raise ValueError("Vast API key not found in configuration.")

    job_configs = []
    
    max_price = 0.10 # max price per node, in dollars
    max_nodes = 3 # max number of nodes to rent
    docker_image = "arfx/distributaur-test-worker" # docker image to use for the worker

    number_of_tasks = 10
    
    function_name = "example_function"

    # Submit params for the job
    for i in range(number_of_tasks):
        job_configs.append({
            "index": i,
            "outputs": [f"result_{i}.txt"],
            "task_params": {"arg1": 1, "arg2": 2},
        })

    # Get the job config
    num_nodes_avail = len(distributaur.search_offers(max_price))
    print("TOTAL NODES AVAILABLE: ", num_nodes_avail)

    # Rent the nodes and get the node ids
    # This will return a list of node ids that you can use to execute tasks
    rented_nodes = distributaur.rent_nodes(
        max_price,
        max_nodes,
        docker_image
    )
    
    # exit with the rented nodes
    atexit.register(handle_exit, rented_nodes)
    
    # Print the rented nodes
    print("TOTAL RENTED NODES: ", len(rented_nodes))
    print(rented_nodes)

    start_monitoring_server()
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
                user_input = input("Files already exist. Do you want to overwrite them? (y/n): ")
                if user_input.lower() == "n":
                    print("Skipping task")
                    skip_task = True
                else:
                    print("Overwriting files")
                    distributaur.delete_file(output)

        if skip_task is False:        
            print("Submitting tasks...")
            
            # queue up the function for execution on the node
            task = distributaur.execute_function(
                    function_name,
                    job_config
                )
            
            # add the task to the list of tasks
            tasks.append(task)

    # Wait for the tasks to complete
    print("Tasks submitted to queue. Waiting for tasks to complete...")
    while not all(task.ready() for task in tasks):
        print("Tasks completed: " + str([task.ready() for task in tasks]))
        print(
            "Tasks remaining: " + str([task for task in tasks if not task.ready()])
        )
        # sleep for a few seconds
        time.sleep(1)

    while True:
        user_input = input("Press q to quit monitoring: ")
        if user_input.lower() == "q":
            print("Stopping monitoring")
            stop_monitoring_server()
            break

    # Terminate the nodes
    distributaur.terminate_nodes(rented_nodes)
    print("Worker process terminated.")
    print('Example completed.')
