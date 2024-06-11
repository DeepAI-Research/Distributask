import os

from ..distributaur import create_from_config

distributaur = create_from_config()


# This is the function that will be executed on the nodes
# You can make your own function and pass in whatever arguments you want
def example_function(index, arg1, arg2):

    # As an ext
    result = arg1 + arg2

    # sleep for 5 seconds to simulate a long running task
    # time.sleep(5)

    # save the result to a file
    with open(f"result_{index}.txt", "w") as f:
        f.write(f"{str(arg1)} plus {str(arg2)} is {str(result)}")

    # write the file to huggingface
    distributaur.upload_file(f"result_{index}.txt")

    # now destroy the file
    os.remove(f"result_{index}.txt")

    # return the result - you can get this value from the task object
    return f"Task {index} completed. Result ({str(arg1)} + {str(arg2)}): {str(result)}"
