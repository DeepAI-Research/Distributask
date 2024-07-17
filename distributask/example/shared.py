import os
import random
import time

from ..distributask import create_from_config

# Create distributask instance
distributask = create_from_config()

# This is the function that will be executed on the nodes
# You can make your own function and pass in whatever arguments you want
def example_function(index, arg1, arg2):

    result = arg1 + arg2

    time.sleep(random.randint(1, 6))

    # Save the result to a file
    with open(f"result_{index}.txt", "w") as f:
        f.write(f"{str(arg1)} plus {str(arg2)} is {str(result)}")

    # Write the file to huggingface
    distributask.upload_file(f"result_{index}.txt")

    # Delete local file
    os.remove(f"result_{index}.txt")

    # Return the result - you can get this value from the task object
    return f"Task {index} completed. Result ({str(arg1)} + {str(arg2)}): {str(result)}"
