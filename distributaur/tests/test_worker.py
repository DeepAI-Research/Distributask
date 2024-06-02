from distributaur.distributaur import Distributaur

distributaur = Distributaur()


# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"


distributaur.register_function(example_function)
