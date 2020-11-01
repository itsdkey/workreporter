import asyncio
import json
import os

from celery.utils.log import get_task_logger
from slack_sdk import WebClient

from reporter.apps import SlackApp
from reporter.bridge import Bridge
from reporter.conf import SLACK_TOKEN
from server.configuration.settings import BASE_DIR

from .celery import app
from .utils import get_redis_instance, validate_text

logger = get_task_logger('server')


@app.task
def display_changelog() -> None:
    """Display changes in a weekly message."""
    path = os.path.dirname(BASE_DIR)
    with open(os.path.join(path, 'CHANGELOG.rst')) as temp:
        changelog = temp.read()

    loop = asyncio.get_event_loop()
    slack_app = SlackApp()
    loop.run_until_complete(
        slack_app.slack.chat_postMessage(
            channel=slack_app.channel_id,
            text=changelog,
        ),
    )


@app.task
def display_pull_requests() -> None:
    """Display pull requests as a newsletter."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Bridge().run())


@app.task
def handle_message(message: dict) -> None:
    """
    Task for handling messages that require more then 3 seconds to execute.

    :param message: a message dict from slack
    """
    logger.debug(f'handle_message task with message: {message}')
    channel = message['channel']
    loop = asyncio.get_event_loop()
    sprint_number = validate_text(message.get('text'))
    if sprint_number:
        logger.debug(f'running for sprint: {sprint_number}')
        bridge = Bridge(sprint_number, channel_id=channel)
        loop.run_until_complete(bridge.run())
    else:
        logger.debug('Sprint number not valid')
        loop.run_until_complete(
            SlackApp().slack.chat_postMessage(
                channel=channel,
                text='Please write in the following syntax "sprint <int>"',
            ),
        )


@app.task
def update_workspace_users() -> None:
    """Update slack's workspace users to Redis."""
    slack = WebClient(token=SLACK_TOKEN)
    users = slack.users_list()
    with get_redis_instance() as redis:
        redis.set('slack-members', json.dumps(users['members']))
