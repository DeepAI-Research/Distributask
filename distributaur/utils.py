import os
import redis
from redis import ConnectionPool

pool = None

def get_redis_values(config):
    print("config is", config)
    host = config.get("REDIS_HOST", "localhost")
    password = config.get("REDIS_PASSWORD", None)
    port = config.get("REDIS_PORT", 6379)
    username = config.get("REDIS_USER", None)
    if password is None:
        redis_url = f"redis://{host}:{port}"
    else:
        redis_url = f"redis://{username}:{password}@{host}:{port}"
    return redis_url

def get_redis_connection(config):
    """Retrieve Redis connection from the connection pool."""
    global pool
    if pool is None:
        redis_url = get_redis_values(config)
        pool = ConnectionPool.from_url(redis_url)
    return redis.Redis(connection_pool=pool)

def close_redis_connection(client):
    """Close the Redis connection."""
    client.close()

def get_env_vars(path=".env.default"):
    env_vars = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                key, value = line.strip().split("=")
                env_vars[key] = value
    return env_vars
