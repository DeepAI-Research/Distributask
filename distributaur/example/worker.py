from .shared import distributaur, example_function

distributaur.register_function(example_function)

celery = distributaur.app
