# core.py

from celery import Celery
from .environment import get_redis_url
from .decorators import register_task

app = Celery("distributaur_tasks", broker=get_redis_url(), backend=get_redis_url())

@app.task(bind=True)
def execute_python_code(self, code):
    try:
        local_scope = {}
        exec(code, {'__builtins__': None}, local_scope)
        return local_scope.get('result', None)  # Assuming the code defines 'result'
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        return None

def submit_task(code):
    """
    Submits a Python code execution task to the Celery worker.
    Args:
        code (str): Python code to execute.

    Returns:
        result: The result of the Python code execution or None if an error occurs.
    """
    try:
        result = app.send_task('execute_python_code', args=[code])
        return result.get(timeout=10)  # Waits for the task to complete and returns the result
    except Exception as e:
        print(f"Failed to submit task: {str(e)}")
        return None
