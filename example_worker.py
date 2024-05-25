# /Users/shawwalters/distributoor/example_worker.py

from distributaur.core import app, register_function
import example

# Ensure the Celery app is available as `celery`
celery = app