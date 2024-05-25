from distributaur.core import configure, register_function, app, get_env_vars, config

env_vars = get_env_vars(".env")
print("env_vars")
print(env_vars)
configure(**env_vars)

# Disable task events
app.conf.worker_send_task_events = False


# Define and register the example_function
def example_function(arg1, arg2):
    return f"Result: arg1={arg1}, arg2={arg2}"


register_function(example_function)
