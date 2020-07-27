import json
from typing import Union

from server.utils import get_redis_instance


def get_value_from_redis(key: str) -> Union[None, str, list, dict]:
    """Get the value from redis if a key exists.

    :param key: the key to look for in Redis.
    """
    value = None
    with get_redis_instance() as redis:
        if redis.exists(key):
            value = json.loads(redis.get(key).decode())
    return value


def set_key_in_redis(key: str, value: Union[list, dict]) -> None:
    """Set a value under a key in Redis."""
    with get_redis_instance() as redis:
        redis.set(key, json.dumps(value))
