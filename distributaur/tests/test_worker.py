from distributaur.core import register_function, app


# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"


register_function(example_function)
