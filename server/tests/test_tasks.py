from io import StringIO

from asynctest import ANY, CoroutineMock, TestCase, patch
from fakeredis import FakeRedis
from slack import WebClient

from reporter.bridge import Bridge

from ..tasks import display_changelog, handle_message


class HandleMessageTestCase(TestCase):
    """TestCase for handle_message task."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class fixture before running tests in the class."""
        cls.fake_redis = FakeRedis()
        cls.task = handle_message

    def setUp(self) -> None:
        """Set up the test fixture before exercising it."""
        self.addCleanup(patch.stopall)
        patch('server.utils.Redis', return_value=self.fake_redis).start()
        self.m_post_message = patch.object(WebClient, 'chat_postMessage', new=CoroutineMock()).start()
        self.bridge_run = patch.object(Bridge, 'run', new=CoroutineMock()).start()

    def tearDown(self) -> None:
        self.fake_redis.flushall()

    def test_task_informs_that_the_message_text_is_not_valid(self):
        """Test task informs that the message's text is not valid."""
        channel = 'channelId123'
        data = {
            'client_msg_id': 'message_id',
            'type': 'message',
            'text': 'This is an example message',
            'user': 'user_id',
            'ts': '1583950633.000800',
            'team': 'teamId123',
            'blocks': [{
                'type': 'rich_text',
                'block_id': '8ye',
                'elements': [{
                    'type': 'rich_text_section',
                    'elements': [{'type': 'text', 'text': 'This is an example message'}],
                }],
            }],
            'channel': channel,
            'event_ts': '1583950633.000800',
            'channel_type': 'channel',
        }
        expected_message = 'Please write in the following syntax "sprint <int>"'

        self.task(data)

        self.m_post_message.assert_awaited_once_with(channel=channel, text=expected_message)

    def test_task_informs_that_the_sprint_number_is_not_valid(self):
        """Test task informs that a number should be passsed after 'sprint '."""
        channel = 'channelId123'
        data = {
            'client_msg_id': 'message_id',
            'type': 'message',
            'text': 'sprint abc',
            'user': 'user_id',
            'ts': '1583950633.000800',
            'team': 'teamId123',
            'blocks': [{
                'type': 'rich_text',
                'block_id': '8ye',
                'elements': [{
                    'type': 'rich_text_section',
                    'elements': [{'type': 'text', 'text': 'sprint abc'}],
                }],
            }],
            'channel': channel,
            'event_ts': '1583950633.000800',
            'channel_type': 'channel',
        }
        expected_message = 'Please write in the following syntax "sprint <int>"'

        self.task(data)

        self.m_post_message.assert_awaited_once_with(channel=channel, text=expected_message)

    def test_task_searches_for_sprints_pull_requests_when_message_text_is_valid(self):
        """Test task runs the Bridge to search for pull request for a given sprint number."""
        channel = 'channelId123'
        data = {
            'client_msg_id': 'message_id',
            'type': 'message',
            'text': 'sprint 392',
            'user': 'user_id',
            'ts': '1583950633.000800',
            'team': 'teamId123',
            'blocks': [{
                'type': 'rich_text',
                'block_id': '8ye',
                'elements': [{
                    'type': 'rich_text_section',
                    'elements': [{'type': 'text', 'text': 'sprint 392'}],
                }],
            }],
            'channel': channel,
            'event_ts': '1583950633.000800',
            'channel_type': 'channel',
        }

        self.task(data)

        self.bridge_run.assert_awaited_once_with()


class HandleChangelogTestCase(TestCase):
    """TestCase for display_changelog task."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class fixture before running tests in the class."""
        cls.fake_redis = FakeRedis()
        cls.task = display_changelog

    def setUp(self) -> None:
        """Set up the test fixture before exercising it."""
        self.addCleanup(patch.stopall)
        self.m_post_message = patch.object(WebClient, 'chat_postMessage', new=CoroutineMock()).start()
        patch('server.utils.Redis', return_value=self.fake_redis).start()

    def tearDown(self) -> None:
        self.fake_redis.flushall()

    @patch('server.tasks.open')
    def test_task_posts_content_of_the_changelog(self, m_open):
        """Test task posts content of the changelog to slack."""
        changelog_content = """
            =========
            CHANGELOG
            =========

            0.0.1 (14.03.2020)
            ------------------

            ** Updates **

            1. Testing changelog
        """
        m_open.return_value = StringIO(changelog_content)

        self.task()

        self.m_post_message.assert_awaited_once_with(channel=ANY, text=changelog_content)
