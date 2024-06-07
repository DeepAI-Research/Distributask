from .shared import distributaur, example_function

distributaur.register_function(example_function)

celery = distributaur.app

if __name__ == "main":
    distributaur.register_function(example_function)
