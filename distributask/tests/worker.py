from ..distributask import create_from_config

distributaur = create_from_config()


# Define and register the test_function
def example_test_function(arg1, arg2):
    return f"Result: arg1+arg2={arg1+arg2}"


celery = distributaur.app


if __name__ == "__main__":
    distributaur.register_function(example_test_function)
