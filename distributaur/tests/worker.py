from distributaur.distributaur import Distributaur

distributaur = Distributaur()


# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1+arg2}"


if __name__ == "__main__":
    distributaur.register_function(example_function)

    celery = distributaur.app