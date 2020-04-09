from typing import Optional

from redis import Redis

from .configuration.settings import (
    REDIS_DATABASE,
    REDIS_PASSWORD,
    REDIS_SOCKET_PATH
)


def validate_text(text: str) -> Optional[int]:
    """
    Validate text message.

    :param text: text to validate
    """
    if text.lower().startswith('sprint '):
        sprint, sprint_number = text.split(' ', 1)
        try:
            sprint_number = int(sprint_number)
        except ValueError:
            return None
        return sprint_number
    return None


def get_redis_instance() -> Redis:
    """Return a Redis instance with the proper configuration."""
    return Redis(db=REDIS_DATABASE, unix_socket_path=REDIS_SOCKET_PATH, password=REDIS_PASSWORD)
