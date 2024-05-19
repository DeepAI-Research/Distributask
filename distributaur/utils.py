# /Users/shawwalters/distributoor/distributaur/utils.py

import os
import redis
from redis import ConnectionPool

pool = None

def get_redis_values(path=".env"):
    env_vars = get_env_vars(path)
    
    host = env_vars.get("REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
    password = env_vars.get("REDIS_PASSWORD", os.getenv("REDIS_PASSWORD", None))
    port = env_vars.get("REDIS_PORT", os.getenv("REDIS_PORT", 6379))
    username = env_vars.get("REDIS_USER", os.getenv("REDIS_USER", None))
    if password is None:
        redis_url = f"redis://{host}:{port}"
    else:
        redis_url = f"redis://{username}:{password}@{host}:{port}"
    return redis_url

def get_redis_connection():
    """Retrieve Redis connection from the connection pool."""
    global pool
    if pool is None:
        redis_url = get_redis_values()
        pool = ConnectionPool.from_url(redis_url)
    return redis.Redis(connection_pool=pool)

def close_redis_connection(client):
    """Close the Redis connection."""
    client.close()

def get_env_vars(path=".env"):
    # combine env vars from .env file and system environment
    
    env_vars = {}
    
    for key, value in os.environ.items():
        env_vars[key] = value
    
    if not os.path.exists(path):
        return env_vars
    with open(path, "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            env_vars[key] = value
    print('*** env vars are:', env_vars)
    return env_vars
