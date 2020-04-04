import asyncio
from typing import Optional
import os

from celery.utils.log import get_task_logger

from server.configuration.settings import BASE_DIR
from reporter.apps import SlackApp
from reporter.bridge import Bridge

from .celery import app

logger = get_task_logger('server')


@app.task
def display_changelog() -> None:
    """Display changes in a weekly message."""
    path = os.path.dirname(BASE_DIR)
    with open(os.path.join(path, 'CHANGELOG.rst')) as temp:
        changelog = temp.read()

    loop = asyncio.get_event_loop()
    slack_app = SlackApp(loop=loop)
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
    loop.run_until_complete(Bridge(loop=loop).run())


@app.task
def handle_message(message: dict) -> None:
    """
    Task for handling messages that require more then 3 seconds to execute.

    :param message: a message dict from slack
    """
    logger.debug(f'handle_message task with message: {message}')
    channel = message['channel']
    loop = asyncio.get_event_loop()
    sprint_number = _validate_text(message.get('text'))
    if sprint_number:
        logger.debug(f'running for sprint: {sprint_number}')
        bridge = Bridge(sprint_number, channel_id=channel, loop=loop)
        loop.run_until_complete(bridge.run())
    else:
        logger.debug('Sprint number not valid')
        loop.run_until_complete(
            SlackApp(loop=loop).slack.chat_postMessage(
                channel=channel,
                text='Please write in the following syntax "sprint <int>"',
            ),
        )


def _validate_text(text: str) -> Optional[int]:
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
