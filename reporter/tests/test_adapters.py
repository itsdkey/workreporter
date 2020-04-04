from json.decoder import JSONDecodeError
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urljoin

from requests.exceptions import ConnectionError, Timeout
from responses import RequestsMock

from ..adapters import BaseAdapter
from ..exceptions import ResponseStatusCodeException


class TestBaseAdapter(TestCase):
    """TestCase for BaseAdapter."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixture before running tests in the class."""
        cls.responses = RequestsMock()
        cls.domain = 'https://example.com'
        cls.path = 'example_path/'

    def setUp(self):
        """Set up the test fixture before exercising it."""
        self.adapter = BaseAdapter(domain=self.domain)

        self.addCleanup(patch.stopall)
        self.responses.start()

    def tearDown(self):
        """Deconstruct the test fixture after testing it."""
        self.responses.stop()
        self.responses.reset()

    def test_get_raises_ConnectionError(self):
        """Test if a ConnectionError was raised."""
        expected_message = 'ERROR:reporter:BaseAdapter (https://example.com/example_path/): An ConnectionError occurred'

        with self.assertLogs('reporter', 'ERROR') as cm:
            with self.assertRaises(ConnectionError):
                self.adapter._get(self.path)
        self.assertEqual(cm.output[0], expected_message)

    def test_get_raises_Timeout(self):
        """Test if a Timeout was raised."""
        self.responses.add(
            self.responses.GET,
            urljoin(self.adapter.domain, self.path),
            body=Timeout(),
        )
        expected_message = 'ERROR:reporter:BaseAdapter (https://example.com/example_path/): An Timeout occurred'

        with self.assertLogs('reporter', 'ERROR') as cm:
            with self.assertRaises(Timeout):
                self.adapter._get(self.path)
        self.assertEqual(cm.output[0], expected_message)

    def test_get_raises_error_when_response_isnt_a_valid_json(self):
        """Test if an error was raised when response isn't a valid json."""
        self.responses.add(
            self.responses.GET,
            urljoin(self.adapter.domain, self.path),
            body='test',
        )
        expected_message = "ERROR:reporter:BaseAdapter (https://example.com/example_path/): response isn't a valid json"

        with self.assertLogs('reporter', 'ERROR') as cm:
            with self.assertRaises(JSONDecodeError):
                self.adapter._get(self.path)
        self.assertEqual(cm.output[0], expected_message)

    def test_get_raises_error_when_status_code_isnt_200(self):
        """Test if an error was raised when status_code isn't 200."""
        status_code = 404
        self.responses.add(
            self.responses.GET,
            urljoin(self.domain, self.path),
            status=status_code,
        )
        expected_log_message = f'ERROR:reporter:' \
                               f'BaseAdapter (https://example.com/example_path/): ' \
                               f'response returned status_code={status_code}'
        expected_message = "BaseAdapter: request didn't return HTTP 200 OK!"

        with self.assertLogs('reporter', 'ERROR') as cm:
            with self.assertRaisesRegex(ResponseStatusCodeException, expected_message):
                self.adapter._get(self.path)
        self.assertEqual(cm.output[0], expected_log_message)

    def test_get_returns_json(self):
        """Test if a json is returned."""
        expected_json = {'test': 1}
        self.responses.add(
            self.responses.GET,
            urljoin(self.adapter.domain, self.path),
            json=expected_json,
        )

        response = self.adapter._get(self.path)

        self.assertEqual(expected_json, response)
