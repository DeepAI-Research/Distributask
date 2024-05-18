from distributaur.task_runner import run_task

@run_task
def run_example_job() -> None:
    print("Running example job")