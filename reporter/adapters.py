import asyncio
from json.decoder import JSONDecodeError
import logging
from urllib.parse import urljoin

from aiohttp import BasicAuth, ClientSession
import requests
from requests.exceptions import ConnectionError, Timeout

from .conf import JIRA_AUTH, JIRA_DOMAIN
from .exceptions import ResponseStatusCodeException
from .parsers import JiraParser

logger = logging.getLogger('reporter')


class BaseAdapter:
    """
    A base adapter for adapters.

    This class should be used as a parent class for all specific adapters.
    """

    auth = None
    domain = None

    def __init__(self, **kwargs):
        """Initialize."""
        self.transport = kwargs.pop('transport', None) or requests
        self.domain = kwargs.pop('domain', None) or self.domain
        self.timeout = 1

    def _get(self, endpoint_path: str, data=None) -> dict:
        url = self._build_url(endpoint_path)
        try:
            response = self.transport.get(url, params=data, auth=self.auth)
        except (ConnectionError, Timeout) as ex:
            logger.error('%s (%s): An %s occurred', self.__class__.__name__, url, ex.__class__.__name__)
            raise

        if response.status_code != 200:
            logger.error('%s (%s): response returned status_code=%s', self.__class__.__name__, url, response.status_code)
            raise ResponseStatusCodeException(f"{self.__class__.__name__}: request didn't return HTTP 200 OK!")

        try:
            return response.json()
        except JSONDecodeError:
            logger.error("%s (%s): response isn't a valid json", self.__class__.__name__, url)
            raise

    def _build_url(self, endpoint_url: str) -> str:
        return urljoin(self.domain, endpoint_url)


class JiraAdapter(BaseAdapter):
    """
    An adapter to communicate with the JIRA API.

    API Documentation:
        https://docs.atlassian.com/software/jira/docs/api/REST/8.1.2/
    """

    auth = JIRA_AUTH
    domain = JIRA_DOMAIN

    def __init__(self, sprint: int):
        """Initialize."""
        super().__init__()
        self.sprint = sprint
        self._parser = JiraParser()

    def get_sprint_board_issues(self) -> list:
        """
        Return the sprint board's issues.

        Support url:
            https://developer.atlassian.com/cloud/jira/software/rest/#api-agile-1-0-sprint-sprintId-issue-get

        """
        endpoint_path = f'agile/1.0/sprint/{self.sprint}/issue'
        data = {
            'jql': 'status="In Review"',
            'fields': ['assignee', 'status', 'summary'],
        }
        response = self._get(endpoint_path, data)
        return self._parser.filter_out_important_data(response)

    async def get_pull_requests(self, issues: list) -> list:
        """
        Return only information about pull requests.

        :param issues: a list of dicts that contain issues information
        """
        tasks = []
        async with ClientSession(auth=BasicAuth(*self.auth)) as session:
            for issue in issues:
                data = {
                    'issueId': issue['id'],
                    'applicationType': 'bitbucket',
                    'dataType': 'pullrequest',
                }
                tasks.append(
                    asyncio.create_task(
                        self._get_pull_requests_for_issue(session, issue, data),
                    ),
                )

            pull_requests = await asyncio.gather(*tasks)

        return self._parser.parse_pull_request_info(pull_requests)

    async def _get_pull_requests_for_issue(self, session: ClientSession, issue: dict, data: dict) -> dict:
        """
        Return pull requests assigned to an issue.

        :param session: a ClientSession
        :param issue: the issue's info
        :param data: the query data that should be sent
        :return: a dictionary containing information about the issue and it's pull requests
        """
        url = self._build_url('dev-status/1.0/issue/detail')
        async with session.get(url, params=data) as resp:
            response = await resp.json()
            response['detail'][0].update(issue)
        return response
