import hashlib
import hmac
import json
from time import time
from unittest.mock import patch
from urllib.parse import urlencode

from fakeredis import FakeRedis
from slack import WebClient
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, url

from server.configuration.application import MyApplication
from server.configuration.settings import SIGNING_SECRET

from ..handlers import HomeHandler, SlackHandler, SprintChangeHandler


class HomeHandlerTestCase(AsyncHTTPTestCase):
    """TestCase for the HomeHandler."""

    def get_app(self) -> Application:
        """Return a Tornado application."""
        app = MyApplication(
            urls=[
                url(r'/', HomeHandler),
            ],
        )
        return app

    def test_get_returns_hello_world_in_response(self):
        """Test get returns hello world in response."""
        response = self.fetch('/')

        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode(), 'Hello world!')


class SlackHandlerTestCase(AsyncHTTPTestCase):
    """TestCase for the SlackHandler."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class fixture before running tests in the class."""
        cls.url = '/slack/events/'
        cls.signing_secret = SIGNING_SECRET
        cls.fake_redis = FakeRedis()

    def setUp(self) -> None:
        """Set up the test fixture before exercising it."""
        super().setUp()
        self.addCleanup(patch.stopall)
        self.task_delay = patch('server.handlers.handle_message.delay').start()
        patch('server.utils.Redis', return_value=self.fake_redis).start()

    def tearDown(self) -> None:
        self.fake_redis.flushall()

    def get_app(self) -> Application:
        """Return a Tornado application."""
        app = MyApplication(
            urls=[
                url(self.url, SlackHandler),
            ],
        )
        return app

    def _prepare_headers(self, body: dict) -> dict:
        """Prepare request headers."""
        timestamp = str(int(time()))
        body = json.dumps(body).encode()
        req = str.encode('v0:' + timestamp + ':') + body
        request_hash = 'v0=' + hmac.new(
            str.encode(self.signing_secret),
            req, hashlib.sha256,
        ).hexdigest()
        return {
            'X-Slack-Request-Timestamp': timestamp,
            'X-Slack-Signature': request_hash,
        }

    def test_post_passes_challenge_from_slack(self):
        """Test post handles the challenge sent from slack."""
        data = {
            'token': 'test1234',
            'challenge': 'my_challenge_test_value',
            'type': 'url_verification',
        }

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=self._prepare_headers(data),
        )

        self.assertEqual(response.code, 200)
        self.assertEqual(response.body.decode(), data['challenge'])

    def test_post_returns_forbidden_when_request_timestamp_is_not_given(self):
        """Test post returns 403 when there is no X-Slack-Request-Timestamp header."""
        data = {
            'token': 'test1234',
            'challenge': 'my_challenge_test_value',
            'type': 'url_verification',
        }
        headers = self._prepare_headers(data)
        headers.pop('X-Slack-Request-Timestamp')

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=headers,
        )

        self.assertEqual(response.code, 403)

    def test_post_returns_forbidden_when_request_timestamp_is_too_old(self):
        """Test post returns 403 when X-Slack-Request-Timestamp header is too old."""
        data = {
            'token': 'test1234',
            'challenge': 'my_challenge_test_value',
            'type': 'url_verification',
        }
        headers = self._prepare_headers(data)
        headers['X-Slack-Request-Timestamp'] = '100'

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=headers,
        )

        self.assertEqual(response.code, 403)

    def test_post_returns_forbidden_when_signature_is_not_given(self):
        """Test post returns 403 when there is no X-Slack-Signature header."""
        data = {
            'token': 'test1234',
            'challenge': 'my_challenge_test_value',
            'type': 'url_verification',
        }
        headers = self._prepare_headers(data)
        headers.pop('X-Slack-Signature')

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=headers,
        )

        self.assertEqual(response.code, 403)

    def test_post_returns_forbidden_when_signature_is_not_valid(self):
        """Test post returns 403 when X-Slack-Signature isn't valid."""
        data = {
            'token': 'test1234',
            'challenge': 'my_challenge_test_value',
            'type': 'url_verification',
        }
        headers = self._prepare_headers(data)
        headers['X-Slack-Signature'] = 'not_valid_signature'

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=headers,
        )

        self.assertEqual(response.code, 403)

    @patch.object(WebClient, 'chat_postMessage')
    def test_post_calls_task_and_posts_pending_message_to_slack_when_message_is_valid(self, m_postmessage):
        """Test post calls thats and informs the user that it will respond in a moment."""
        channel = 'testchannel'
        data = {
            'token': 'test_token',
            'team_id': 'teamId123',
            'api_app_id': 'appId123',
            'event': {
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
                'channel_type': 'im',
            },
            'type': 'event_callback',
            'event_id': 'EvUVFHBRNE',
            'event_time': 1583950633,
            'authed_users': ['user_id234'],
        }

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=self._prepare_headers(data),
        )

        self.assertEqual(response.code, 200)
        self.assertTrue(self.task_delay.called)
        m_postmessage.assert_called_once_with(channel=channel, text="I'll respond in a moment...")

    @patch.object(WebClient, 'chat_postMessage')
    def test_post_does_nothing_when_message_is_not_from_an_valid_channel(self, m_postmessage):
        """Test if a message is handled when it came from a channel_type=channel."""
        data = {
            'token': 'test_token',
            'team_id': 'teamId123',
            'api_app_id': 'appId123',
            'event': {
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
                'channel': 'testchannelId',
                'event_ts': '1583950633.000800',
                'channel_type': 'channel',
            },
            'type': 'event_callback',
            'event_id': 'EvUVFHBRNE',
            'event_time': 1583950633,
            'authed_users': ['user_id234'],
        }

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=self._prepare_headers(data),
        )

        self.assertEqual(response.code, 200)
        self.task_delay.assert_not_called()
        m_postmessage.assert_not_called()

    @patch.object(WebClient, 'chat_postMessage')
    def test_post_does_nothing_when_message_is_a_bot_response(self, m_postmessage):
        """Test if a message is handled when the message was sent by a bot."""
        data = {
            'token': 'test_token',
            'team_id': 'teamId123',
            'api_app_id': 'appId123',
            'event': {
                'bot_id': 'botId1234',
                'type': 'message',
                'text': 'Please write in the following syntax "sprint &lt;int&gt;"',
                'user': 'userId12',
                'ts': '1583951653.001100',
                'team': 'teamId123',
                'bot_profile': {
                    'id': 'botId1234',
                    'deleted': False,
                    'name': 'PRreminder',
                    'updated': 1582571467,
                    'app_id': 'appId123',
                    'icons': {
                        'image_36': 'https://avatars.slack-edge.com/example_36.jpg',
                        'image_48': 'https://avatars.slack-edge.com/example_48.jpg',
                        'image_72': 'https://avatars.slack-edge.com/example_72.jpg',
                    },
                    'team_id': 'teamId123',
                },
                'channel': 'channel_id_1234',
                'event_ts': '1583951653.001100',
                'channel_type': 'im',
            },
            'type': 'event_callback',
            'event_id': 'EvV8AGHBLG',
            'event_time': 1583951653,
            'authed_users': ['userId1'],
        }

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=self._prepare_headers(data),
        )

        self.assertEqual(response.code, 200)
        self.task_delay.assert_not_called()
        m_postmessage.assert_not_called()

    @patch.object(WebClient, 'chat_postMessage')
    def test_post_does_nothing_when_message_is_a_retry(self, m_postmessage):
        """Test if a message is handled when the message was sent as a retry message."""
        data = {
            'token': 'test_token',
            'team_id': 'teamId123',
            'api_app_id': 'appId123',
            'event': {
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
                'channel': 'ChannelId',
                'event_ts': '1583950633.000800',
                'channel_type': 'im',
            },
            'type': 'event_callback',
            'event_id': 'EvUVFHBRNE',
            'event_time': 1583950633,
            'authed_users': ['user_id234'],
        }
        headers = self._prepare_headers(data)
        headers['X-Slack-Retry-Num'] = '1'

        response = self.fetch(
            self.url,
            method='POST',
            body=json.dumps(data),
            headers=headers,
        )

        self.assertEqual(response.code, 200)
        self.task_delay.assert_not_called()
        m_postmessage.assert_not_called()


class SprintChangeHandlerTestCase(AsyncHTTPTestCase):
    """TestCase for the SprintChangeHandler."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class fixture before running tests in the class."""
        cls.url = '/sprint/change/'
        cls.fake_redis = FakeRedis()

    def setUp(self) -> None:
        """Set up the test fixture before exercising it."""
        super().setUp()
        self.addCleanup(patch.stopall)
        patch('server.utils.Redis', return_value=self.fake_redis).start()

        self.data = {
            'channel_id': 'CTHGW076H',
            'channel_name': 'testdave',
            'command': '/changesprint',
            'response_url': 'https://hooks.slack.com/commands/T06KLH51S/1265250490467/bwB31VdEEgRXkWk4m4jqxIj8',
            'team_domain': 'beefee',
            'team_id': 'T06KLH51S',
            'text': '400',
            'token': 'gu8mEk574ugENdhcg8adgywv',
            'trigger_id': '1271230064692.6666583060.8555f8ead3a8c30615121b28149e891b',
            'user_id': 'TEST1234',
            'user_name': 'joe.doe',
        }

    def tearDown(self) -> None:
        self.fake_redis.flushall()

    def get_app(self) -> Application:
        """Return a Tornado application."""
        app = MyApplication(
            urls=[
                url(self.url, SprintChangeHandler),
            ],
        )
        return app

    def test_saves_sprint_number_into_redis_when_valid(self):
        expected_value = int(self.data['text'])

        response = self.fetch(
            self.url,
            method='POST',
            body=urlencode(self.data),
        )

        value = self.fake_redis.get('sprint-number').decode('utf-8')
        self.assertEqual(response.code, 200)
        self.assertEqual(expected_value, int(value))

    def test_does_not_save_sprint_number_when_it_is_invalid(self):
        self.data['text'] = 'test'

        response = self.fetch(
            self.url,
            method='POST',
            body=urlencode(self.data),
        )

        self.assertEqual(response.code, 200)
        self.assertFalse(self.fake_redis.exists('sprint-number'))
