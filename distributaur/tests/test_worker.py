from distributaur.task_runner import configure, register_function, app
from distributaur.utils import get_env_vars

env_vars = get_env_vars()
configure(**env_vars)

# Ensure the Celery app is available as `celery`
celery = app

# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"

register_function(example_function)
