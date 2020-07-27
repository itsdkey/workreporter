import hashlib
import hmac
from time import time
from typing import Awaitable, Optional

from tornado.escape import json_decode
from tornado.web import HTTPError, RequestHandler, access_log

from reporter.apps import SlackApp
from server.configuration.settings import SIGNING_SECRET

from .tasks import handle_message
from .utils import get_redis_instance


class HomeHandler(RequestHandler):
    """Home page handler."""

    def get(self) -> None:
        """HTTP get."""
        self.write('Hello world!')


class SlackHandler(RequestHandler):
    """Main handler for the server."""

    signing_secret = SIGNING_SECRET

    def prepare(self) -> Optional[Awaitable[None]]:
        """Execute at the beginning of a request before  `get`/`post`/etc."""
        request_timestamp = self.request.headers.get('X-Slack-Request-Timestamp')
        if not request_timestamp:
            access_log.error("Request doesn't have X-Slack-Request-Timestamp")
            self.set_status(403, "Request doesn't have a required header")
            raise HTTPError(403)
        if abs(time() - int(request_timestamp)) > 60 * 5:
            access_log.error('Invalid timestamp')
            self.set_status(403, 'Invalid request timestamp')
            raise HTTPError(403)

        # Verify the request signature using the app's signing secret
        # raise an error if the signature can't be verified
        request_signature = self.request.headers.get('X-Slack-Signature')
        if not request_signature:
            access_log.error("Request doesn't have X-Slack-Signature")
            self.set_status(403, "Request doesn't have a required header")
            raise HTTPError(403)
        if not self._verify_signature(request_timestamp, request_signature):
            access_log.error('Invalid signature')
            self.set_status(403, 'Invalid request signature')
            raise HTTPError(403)

    def _verify_signature(self, timestamp: str, signature: str) -> bool:
        """
        Verify the request signature of the request sent from Slack.

        Generate a new hash using the app's signing secret and request data and
        compare the generated hash and incoming request signature.

        :param timestamp: X-Slack-Request-Timestamp value
        :param signature: X-Slack-Signature value
        :return: True if hashes are equal
        """
        req = str.encode('v0:' + str(timestamp) + ':') + self.request.body
        request_hash = 'v0=' + hmac.new(
            str.encode(self.signing_secret),
            req, hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(request_hash, signature)

    def post(self) -> None:
        """Handle the HTTP POST method."""
        body = json_decode(self.request.body)
        access_log.debug(body)
        if body.get('challenge'):
            self.write(body['challenge'])
            return

        message = self._validate_message(body.get('event'))
        if message:
            channel = message['channel']
            access_log.debug(f'Scheduling task...')
            handle_message.delay(message)
            slack_app = SlackApp()
            slack_app.slack.chat_postMessage(channel=channel, text="I'll respond in a moment...")

    def _validate_message(self, message: dict) -> Optional[dict]:
        """
        Validate a message if it should be handled.

        :param message: a message from slack
        """
        if message.get('bot_profile'):
            access_log.debug("Bot message, it shouldn't be handled.")
            return None
        channel_type = message.get('channel_type')
        if channel_type != 'im':
            access_log.debug(f"Channel isn't a direct message channel. Channel type: {channel_type}")
            return None
        if self.request.headers.get('X-Slack-Retry-Num'):
            access_log.error(f'Muting retires: {self.request.headers.get("X-Slack-Retry-Num")}')
            return None
        return message


class SprintChangeHandler(RequestHandler):
    """Class for handling sprint change slash command from slack API."""

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def post(self) -> None:
        """Handle the HTTP POST method."""
        slack_app = SlackApp()
        sprint_number = self._validate_message(self.get_argument('text'))
        if not sprint_number:
            slack_app.slack.chat_postMessage(
                channel=slack_app.channel_id,
                text=f"You've passed an invalid sprint number: {self.get_argument('text')}."
                     f' Please follow this syntax: <int>',
            )
            return

        with get_redis_instance() as redis:
            redis.set('sprint-number', sprint_number)
        slack_app.slack.chat_postMessage(
            channel=slack_app.channel_id,
            text=f'Sprint number set to {sprint_number}...',
        )

    def _validate_message(self, sprint_number: str) -> Optional[int]:
        """
        Validate the text sent to this endpoint.
        It should be an sprint number <int>.

        :param sprint_number: a sprint number
        """
        try:
            value = int(sprint_number)
        except ValueError:
            error = f'Invalid sprint number! Required int, got "{sprint_number}"'
            access_log.error(error)
            return None
        return value
