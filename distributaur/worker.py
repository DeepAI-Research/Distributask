from distributaur.decorators import register_task

@register_task
def execute_python_code(code):
    try:
        local_scope = {}
        exec(code, {'__builtins__': None}, local_scope)
        return local_scope.get('result', None)  # Assuming the code defines 'result'
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        return None
