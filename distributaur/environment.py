import os

def get_redis_url():
    """Constructs the Redis connection URL from environment variables."""
    host = os.getenv("REDIS_HOST", "localhost")
    password = os.getenv("REDIS_PASSWORD", None)
    port = os.getenv("REDIS_PORT", 6379)
    return f"redis://:{password}@{host}:{port}" if password else f"redis://{host}:{port}"

def get_env_vars():
    """Loads environment variables critical for Distributaur operations."""
    required_vars = ["VAST_API_KEY", "REDIS_HOST", "REDIS_PORT"]
    env_vars = {var: os.getenv(var) for var in required_vars}
    if not all(env_vars.values()):
        missing = [var for var, value in env_vars.items() if not value]
        raise EnvironmentError(f"Missing critical environment variables: {', '.join(missing)}")
    return env_vars
