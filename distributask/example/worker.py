from .shared import distributask, example_function

# Register function to worker using distributask instance
distributask.register_function(example_function)

# Create Celery worker
celery = distributask.app
