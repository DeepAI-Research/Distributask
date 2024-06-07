import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "./"))

from distributaur.example.shared import distributaur, example_function

celery = distributaur.app

if __name__ == "main":
    distributaur.register_function(example_function)
