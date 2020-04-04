from unittest import TestCase

from ..slughify import slughifi


class SlughifiTestCase(TestCase):
    """TestCase for slughifi function."""

    def test_slughifi_slugs_polish_chars(self):
        """Test if polish chars were converted."""
        name = 'ąśćłóźż'
        expected_result = 'asclozz'

        result = slughifi(name)

        self.assertEqual(result.decode('utf-8'), expected_result)

    def test_slughifi_returns_char_when_not_in_map(self):
        """Test checking if a char was returned when not found in the mapping."""
        name = '!'

        result = slughifi(name)

        self.assertEqual(result.decode('utf-8'), name)
