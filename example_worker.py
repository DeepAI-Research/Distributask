# /Users/shawwalters/distributoor/example_worker.py

from distributaur.task_runner import app
import example

# Ensure the Celery app is available as `celery`
celery = app