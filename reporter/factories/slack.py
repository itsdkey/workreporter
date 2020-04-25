import string

from factory import Dict, DictFactory, Faker, List
from factory.fuzzy import FuzzyChoice, FuzzyText

from reporter.apps import __version__


class SectionButtonFactory(DictFactory):
    """A factory for a section with a button."""

    type = 'section'
    accessory = Dict({
        'text': {
            'emoji': True,
            'text': 'Review Now',
            'type': 'plain_text',
        },
        'type': 'button',
        'url': FuzzyText(
            prefix='https://bitbucket.org/example/example_repos/pull-requests/',
            length=4,
            chars=string.digits,
        ),
    })
    text = Dict({
        'text': FuzzyText(prefix='<@', suffix='>', length=2, chars=string.digits),
        'type': 'mrkdwn',
    })


class SectionBlockFactory(DictFactory):
    """A factory for a section block."""

    type = 'section'
    text = Dict({
        'text': Dict({
            'text': Faker('sentence'),
            'type': FuzzyChoice(['mrkdwn', 'plain_text']),
        }),
    })


class ContextBlockFactory(DictFactory):
    """A factory for a context block."""

    type = 'context'
    elements = List([
        Dict({'text': '*Author:* dave', 'type': 'mrkdwn'}),
        Dict({'text': f'*version:* {__version__}', 'type': 'mrkdwn'}),
    ])


class DividerBlockFactory(DictFactory):
    """A factory for a divider block."""

    type = 'divider'


class BlockFactory(DictFactory):
    """A factory for a block used in slack messages."""

    text = Dict({
        'text': Dict({
            'text': Faker('sentence'),
            'type': FuzzyChoice(['mrkdwn', 'plain_text']),
            'emoji': FuzzyChoice([True, False]),
        }),
    })
    type = FuzzyChoice(['section', 'divider', 'context'])


class SlackMessageFactory(DictFactory):
    """A factory for a slack message."""

    blocks = List([
        SectionBlockFactory(),
        ContextBlockFactory(),
        DividerBlockFactory(),
        SectionButtonFactory(),
        SectionButtonFactory(),
        DividerBlockFactory(),
    ])
