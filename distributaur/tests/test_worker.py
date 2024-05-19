# /Users/shawwalters/distributoor/example_worker.py

from distributaur.task_runner import register_function, app

# Ensure the Celery app is available as `celery`
celery = app

# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"

register_function(example_function)
