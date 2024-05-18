import json
import subprocess
import sys
import os
import ssl
import time
from celery import Celery
from redis import ConnectionPool, Redis

ssl._create_default_https_context = ssl._create_unverified_context

from distributaur.utils import get_redis_values

redis_url = get_redis_values()
pool = ConnectionPool.from_url(redis_url)
redis_client = Redis(connection_pool=pool)

app = Celery("tasks", broker=redis_url, backend=redis_url)


def run_task(task_func):
    @app.task(name=task_func.__name__, acks_late=True, reject_on_worker_lost=True)
    def wrapper(*args, **kwargs):
        job_id = kwargs.get("job_id")
        task_id = wrapper.request.id
        print(f"Starting task {task_id} in job {job_id}")
        update_task_status(job_id, task_id, "IN_PROGRESS")

        timeout = 600  # 10 minutes in seconds
        task_timeout = 2700  # 45 minutes in seconds

        start_time = time.time()
        print(f"Task {task_id} starting.")

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                update_task_status(task_id, "TIMEOUT")
                print(f"Task {task_id} timed out before starting task")
                return

            try:
                task_start_time = time.time()
                print(f"Task {task_id} executing task function.")
                result = task_func(*args, **kwargs)
                print(f"Task {task_id} completed task function.")

                elapsed_task_time = time.time() - task_start_time
                if elapsed_task_time > task_timeout:
                    update_task_status(task_id, "TIMEOUT")
                    print(
                        f"Task {task_id} timed out after {elapsed_task_time} seconds of execution"
                    )
                    return

                update_task_status(task_id, "COMPLETE")
                print(f"Task {task_id} completed successfully")
                return result

            except subprocess.TimeoutExpired:
                update_task_status(task_id, "TIMEOUT")
                print(f"Task {task_id} timed out after {timeout} seconds")
                return

            except Exception as e:
                update_task_status(job_id, task_id, "FAILED")
                print(f"Task {task_id} failed with error: {str(e)}")
                return

    return wrapper


def update_task_status(job_id, task_id, status):
    key = f"celery-task-meta-{task_id}"
    value = json.dumps({"status": status})
    redis_client.set(key, value)
    print(f"Updated status for task {task_id} in job {job_id} to {status}")


if __name__ == "__main__":
    print("Starting Celery worker...")
    app.start(argv=["celery", "worker", "--loglevel=info"])
