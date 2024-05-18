def register_task(app):
    def decorator(func):
        task = app.task(bind=True)(func)
        return func
    return decorator