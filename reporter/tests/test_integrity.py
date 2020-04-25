from unittest.mock import ANY

from aiohttp import ClientSession
from asynctest import CoroutineMock, MagicMock, TestCase, patch
from factory import Iterator
from fakeredis import FakeRedis
from responses import RequestsMock
from slack import WebClient

from ..bridge import Bridge
from ..factories.bitbucket import (
    BitBucketIssueFactory,
    BitBucketResponseFactory,
    PullRequestFactory,
    ReviewerFactory,
)
from ..factories.jira import (
    JiraIssueFactory,
    JiraResponseFactory,
    StatusFactory,
)
from ..factories.slack import (
    ContextBlockFactory,
    DividerBlockFactory,
    SectionBlockFactory,
    SectionButtonFactory,
    SlackMessageFactory,
)


class TestIntegrity(TestCase):
    """TestCase for integrity tests. In this TestCase we try to pass the whole flow."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixture before running tests in the class."""
        cls.sprint = 388
        cls.jira_sprint_api_url = f'https://empsgourp.atlassian.net/rest/agile/1.0/sprint/{cls.sprint}/issue'
        cls.jira_dev_tools_api_url = 'https://empsgourp.atlassian.net/rest/dev-status/1.0/issue/detail'

        cls.fake_redis = FakeRedis()
        cls.responses = RequestsMock()

    def setUp(self):
        """Set up the test fixture before exercising it."""
        self.responses.start()

        self.addCleanup(patch.stopall)
        patch('reporter.utils.get_redis_instance', return_value=self.fake_redis).start()
        self.patcher = patch.object(WebClient, 'chat_postMessage', new=CoroutineMock())
        self.chat_postMessage = self.patcher.start()
        patch.object(WebClient, 'users_list', new=CoroutineMock(return_value=self._get_users_list())).start()
        self.m_get = patch.object(ClientSession, 'get', return_value=MagicMock()).start()

        self.bridge = Bridge(self.sprint)

    def tearDown(self):
        """Deconstruct the test fixture after testing it."""
        self.responses.stop()
        self.responses.reset()
        self.fake_redis.flushall()

    @staticmethod
    def _get_users_list():
        return {
            'ok': True,
            'members': [
                {'id': '1', 'real_name': 'Mary Mary1'},
                {'id': '2', 'real_name': 'Mary Mary2'},
                {'id': '3', 'real_name': 'Mery Mery3'},
                {'id': '4', 'real_name': 'Mery Mery4'},
                {'id': '5', 'real_name': 'Jeff1'},
                {'id': '6', 'real_name': 'Jeff2'},
                {'id': '7', 'real_name': 'Jeff3'},
                {'id': '8', 'real_name': 'Jeff4'},
                {'id': '9', 'real_name': 'Ben1'},
                {'id': '10', 'real_name': 'Ben2'},
                {'id': '11', 'real_name': 'Ben3'},
                {'id': '12', 'real_name': 'Ben4'},
                {'id': '13', 'real_name': 'Tom1'},
                {'id': '14', 'real_name': 'Tom2'},
                {'id': '15', 'real_name': 'Tom3'},
                {'id': '16', 'real_name': 'Tom4'},
            ],
        }

    @staticmethod
    def _get_expected_no_pull_request_message():
        """Get expected message that should be sent when there no pull requests exist."""
        return SlackMessageFactory.create(
            blocks=[
                SectionBlockFactory.create(
                    text__text=':bell:  *Pull requests report*  :bell:',
                    text__type='mrkdwn',
                ),
                ContextBlockFactory.create(),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f'No pull requests. Good Job everyone! :v:',
                    text__type='plain_text',
                    text__emoji=True,
                ),
                DividerBlockFactory.create(),
            ],
        )

    def test_post_one_issue_in_review_without_pull_requests_should_send_default_message_to_slack(self):
        """
        Test a situation where there was a issue IN REVIEW but without any pull requests.

        In this situation the Sprint board contained only one issue and it has a IN REVIEW status.
        A default message should be send to slack because there are no pull requests.
        """
        jira_issue = JiraResponseFactory.create(
            issues=[
                JiraIssueFactory.create(fields__status=StatusFactory.create(name='In Review')),
            ],
        )
        bitbucket_issue = BitBucketResponseFactory.create(
            detail=[
                BitBucketIssueFactory.create(pullRequests=[]),
            ],
        )
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_issue,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value=bitbucket_issue)
        expected_message = self._get_expected_no_pull_request_message()

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)

    def test_post_one_issue_in_review_with_one_pull_request_should_send_a_message_to_slack(self):
        """
        Test a situation where there was a issue IN REVIEW with a pull request to check.

        In this situation the Sprint board contained only one issue, with a IN REVIEW status and it has a pull request.
        A message should be send to slack with that pull request info.
        """
        jira_response = JiraResponseFactory.create(
            issues=[
                JiraIssueFactory.create(fields__status=StatusFactory.create(name='In Review')),
            ],
        )
        key, title = (jira_response['issues'][0]['key'], jira_response['issues'][0]['fields']['summary'])
        bitbucket_issue = BitBucketIssueFactory.create(
            pullRequests=[
                PullRequestFactory.create(
                    status='OPEN',
                    reviewers=ReviewerFactory.create_batch(3, approved=False),
                ),
            ],
        )
        bitbucket_response = BitBucketResponseFactory.create(detail=[bitbucket_issue])
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_response,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value=bitbucket_response)
        expected_message = SlackMessageFactory.create(
            blocks=[
                SectionBlockFactory.create(
                    text__text=':bell:  *Pull requests report*  :bell:',
                    text__type='mrkdwn',
                ),
                ContextBlockFactory.create(),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{key}] {title}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issue['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issue['pullRequests'][0]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
            ],
        )

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)

    def test_post_one_issue_in_review_with_many_pull_requests_should_send_a_message_to_slack(self):
        """
        Test a situation where there was a issue IN REVIEW with many pull requests to check.

        In this situation the Sprint board contained only one issue, with a IN REVIEW status and it has multiple
        pull requests.
        A message should be send to slack with pull request infos.
        """
        jira_response = JiraResponseFactory.create(
            issues=[
                JiraIssueFactory.create(fields__status=StatusFactory.create(name='In Review')),
            ],
        )
        key, title = (jira_response['issues'][0]['key'], jira_response['issues'][0]['fields']['summary'])
        bitbucket_issue = BitBucketIssueFactory.create(
            pullRequests=PullRequestFactory.create_batch(
                size=2,
                status='OPEN',
                reviewers=ReviewerFactory.create_batch(3, approved=False),
            ),
        )
        bitbucket_response = BitBucketResponseFactory.create(detail=[bitbucket_issue])
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_response,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(return_value=bitbucket_response)
        expected_message = SlackMessageFactory.create(
            blocks=[
                SectionBlockFactory.create(text__text=':bell:  *Pull requests report*  :bell:', text__type='mrkdwn'),
                ContextBlockFactory.create(),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{key}] {title}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issue['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issue['pullRequests'][0]['reviewers']
                    ]),
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issue['pullRequests'][1]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issue['pullRequests'][1]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
            ],
        )

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)

    def test_post_two_issues_in_review_without_pull_requests_should_send_default_message_to_slack(self):
        """
        Test a situation where there were two issues IN REVIEW but without any pull requests.

        In this situation the Sprint board contained two issues and they have IN REVIEW statuses.
        A default message should be send to slack because there are no pull requests.
        """
        jira_issues = JiraResponseFactory.create(
            issues=JiraIssueFactory.create_batch(size=2, fields__status=StatusFactory.create(name='In Review')),
        )
        bitbucket_issues = BitBucketIssueFactory.create_batch(
                size=len(jira_issues['issues']),
                pullRequests=[],
        )
        bitbucket_responses = BitBucketResponseFactory.create_batch(
            size=2,
            detail=Iterator([
                [bitbucket_issues[0]],
                [bitbucket_issues[1]],
            ]),
        )
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_issues,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=bitbucket_responses)
        expected_message = self._get_expected_no_pull_request_message()

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)

    def test_post_two_issue_in_review_with_one_pull_request_should_send_a_message_to_slack(self):
        """
        Test a situation where there were two issues IN REVIEW with pull requests to check.

        In this situation the Sprint board contained two issues, with IN REVIEW statuses and they have a pull requests.
        A message should be send to slack with pull requests infos.
        """
        jira_response = JiraResponseFactory.create(
            issues=JiraIssueFactory.create_batch(size=2, fields__status=StatusFactory.create(name='In Review')),
        )
        keys, titles = (
            (jira_response['issues'][0]['key'], jira_response['issues'][1]['key']),
            (jira_response['issues'][0]['fields']['summary'], jira_response['issues'][1]['fields']['summary']),
        )
        bitbucket_issues = BitBucketIssueFactory.create_batch(
            size=2,
            pullRequests=[
                PullRequestFactory.create(
                    status='OPEN',
                    reviewers=ReviewerFactory.create_batch(3, approved=False),
                ),
            ],
        )
        bitbucket_responses = BitBucketResponseFactory.create_batch(
            size=2,
            detail=Iterator([
                [bitbucket_issues[0]],
                [bitbucket_issues[1]],
            ]),
        )
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_response,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=bitbucket_responses)
        expected_message = SlackMessageFactory.create(
            blocks=[
                SectionBlockFactory.create(text__text=':bell:  *Pull requests report*  :bell:', text__type='mrkdwn'),
                ContextBlockFactory.create(),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{keys[0]}] {titles[0]}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[0]['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[0]['pullRequests'][0]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{keys[1]}] {titles[1]}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[1]['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[1]['pullRequests'][0]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
            ],
        )

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)

    def test_post_two_issue_in_review_with_many_pull_requests_should_send_a_message_to_slack(self):
        """
        Test a situation where there were two issues IN REVIEW with many pull requests to check.

        In this situation the Sprint board contained two issues, with IN REVIEW statuses and they have multiple
        pull requests.
        A message should be send to slack with pull request infos.
        """
        jira_response = JiraResponseFactory.create(
            issues=JiraIssueFactory.create_batch(size=2, fields__status=StatusFactory.create(name='In Review')),
        )
        keys, titles = (
            (jira_response['issues'][0]['key'], jira_response['issues'][1]['key']),
            (jira_response['issues'][0]['fields']['summary'], jira_response['issues'][1]['fields']['summary']),
        )
        bitbucket_issues = BitBucketIssueFactory.create_batch(
            size=2,
            pullRequests=PullRequestFactory.create_batch(
                size=2,
                status='OPEN',
                reviewers=ReviewerFactory.create_batch(3, approved=False),
            ),
        )
        bitbucket_responses = BitBucketResponseFactory.create_batch(
            size=2,
            detail=Iterator([
                [bitbucket_issues[0]],
                [bitbucket_issues[1]],
            ]),
        )
        self.responses.add(
            self.responses.GET,
            self.jira_sprint_api_url,
            json=jira_response,
        )
        self.m_get.return_value.__aenter__.return_value.json = CoroutineMock(side_effect=bitbucket_responses)
        expected_message = SlackMessageFactory.create(
            blocks=[
                SectionBlockFactory.create(text__text=':bell:  *Pull requests report*  :bell:', text__type='mrkdwn'),
                ContextBlockFactory.create(),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{keys[0]}] {titles[0]}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[0]['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[0]['pullRequests'][0]['reviewers']
                    ]),
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[0]['pullRequests'][1]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[0]['pullRequests'][1]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
                SectionBlockFactory.create(
                    text__text=f':bender: *[{keys[1]}] {titles[1]}*',
                    text__type='mrkdwn',
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[1]['pullRequests'][0]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[1]['pullRequests'][0]['reviewers']
                    ]),
                ),
                SectionButtonFactory.create(
                    accessory__url=bitbucket_issues[1]['pullRequests'][1]['url'],
                    text__text=' '.join([
                        f'{r["name"]}' for r in bitbucket_issues[1]['pullRequests'][1]['reviewers']
                    ]),
                ),
                DividerBlockFactory.create(),
            ],
        )

        self.loop.run_until_complete(self.bridge.run())

        self.chat_postMessage.assert_awaited_once_with(channel=ANY, **expected_message)
