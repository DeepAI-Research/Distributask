from .shared import distributask, example_function

distributask.register_function(example_function)

celery = distributask.app
