import asyncio
from copy import deepcopy
import json
import os
from typing import Optional

from slack import WebClient

from .adapters import JiraAdapter
from .conf import SLACK_CHANNEL_ID, SLACK_TOKEN
from .slughify import slughifi
from .utils import get_value_from_redis, set_key_in_redis

__version__ = '0.0.4'


class JiraApp:
    """A class responsible for logic related to Jira."""

    def __init__(self, sprint: int = None, **kwargs):
        """
        Initialize.

        :param sprint_number: a number of the sprint to search
        :param kwargs: additional values such as filter name and value for
            the filter
        """
        self.adapter = JiraAdapter(sprint)

    async def run(self) -> list:
        """Run the process for a given sprint board."""
        issues = self.adapter.get_sprint_board_issues()
        pull_requests = await self.adapter.get_pull_requests(issues)
        return pull_requests


class SlackApp:
    """A class responsible for logic related to Slack."""

    def __init__(self, **kwargs):
        """Initialize."""
        loop = kwargs.get('loop') or asyncio.get_event_loop()

        self.version = f'*version:* {__version__}'
        self.channel_id = kwargs.get('channel_id') or SLACK_CHANNEL_ID
        self.known_user_ids = get_value_from_redis('slack-known-user-ids') or {}

        self.slack = WebClient(token=SLACK_TOKEN, loop=loop, run_async=True)

    @staticmethod
    def _render_template(filename: str) -> dict:
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, 'templates', filename)
        with open(path) as json_template:
            template = json.load(json_template)
        return template

    async def remind_about_pull_requests(self, pull_requests: list) -> None:
        """
        Send a reminder about pull requests.

        :param pull_requests: information about the pull requests
        """
        header = self._render_template('header.json')
        author = self._render_template('author.json')
        author['elements'][1]['text'] = self.version
        divider = self._render_template('divider.json')
        title_block = self._render_template('title.json')
        description_block = self._render_template('description.json')
        message = {
            'blocks': [
                header,
                author,
                divider,
            ],
        }
        for issue in pull_requests:
            title = deepcopy(title_block)
            descriptions = []
            for pull_request in issue['pull_requests']:
                description = deepcopy(description_block)
                reviewers = map(
                    lambda name: self._get_user_mention(name),
                    pull_request['reviewers'],
                )
                description['text']['text'] = ' '.join(reviewers)
                description['accessory']['url'] = pull_request['url']
                descriptions.append(description)

            if descriptions:
                title['text']['text'] = f':bender: *[{issue["key"]}] {issue["title"]}*'
                message['blocks'].extend([title] + descriptions + [divider])

        set_key_in_redis('slack-known-user-ids', self.known_user_ids)
        await self.send_message(message)

    def _get_user_mention(self, name: str) -> str:
        """
        Get text for a user mention.

        Typically it should be '<@USER_ID>' where USER_ID is a slack user's id but if a user wasn't found then
        it will return his name.

        :param name: a user's name from a pull request

        :returns: a mention string
        """
        try:
            return self.known_user_ids[name]
        except KeyError:
            pass

        mention = name
        users = get_value_from_redis('slack-members') or []
        user = self._get_user(name, users)
        if user:
            mention = f'<@{user["id"]}>'

        self.known_user_ids[name] = mention

        return mention

    def _get_user(self, name: str, users: list, first_time=True) -> Optional[dict]:
        """
        Get user from slack users.

        :param name: the name of a reviewer
        :param users: a list of users assigned to a slack workspace
        :param first_time: a boolean to control if this is the first call (for recursion break)
        """
        try:
            user = next(filter(lambda x: x['profile'].get('real_name_normalized') == name, users))
        except StopIteration:
            name = slughifi(name).decode('utf-8')
            if first_time:
                return self._get_user(name, users, first_time=False)
            return None
        return user

    async def send_no_pull_requests_message(self) -> None:
        """Send a default message when no pull requests."""
        message = self._render_template('no_pull_requests.json')
        message['blocks'][1]['elements'][1]['text'] = self.version
        await self.send_message(message)

    async def send_message(self, message: dict) -> None:
        """
        Send a message to slack.

        :param message: a dictionary that contains blocks that will be used as
            JSON message to slack.
        """
        await self.slack.chat_postMessage(channel=self.channel_id, **message)
