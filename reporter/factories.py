import string
from uuid import uuid4

from factory import Dict, DictFactory, Faker, LazyAttribute, List, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText

from .apps import __version__


class AssigneeFactory(DictFactory):
    """A factory for the assignee dict returned by the JIRA api."""

    accountId = str(uuid4())
    accountType = 'atlassian'
    active = True
    avatarUrls = Dict(
        {f'{i}x{i}': f'https://example.com/128?size={i}&s={i}' for i in [16, 24, 32, 64]},
    )
    displayName = Faker('name')
    emailAddress = LazyAttribute(lambda x: f'{x.displayName.lower().replace(" ", ".")}@example.com')
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/2/user=accountId={x.accountId}')
    timeZone = 'Europe/Warsaw'


class StatusFactory(DictFactory):
    """A factory for the status dict returned by the JIRA api."""

    description = Faker('sentence')
    id = FuzzyInteger(10000, 100000)
    name = FuzzyChoice(['New', 'In Progress', 'In Review', 'Reviewed', 'To Deploy', 'Done'])
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/2/status/{x.id}')


class JiraIssueFactory(DictFactory):
    """A factory for a issue returned from the JIRA api."""

    id = FuzzyInteger(10000, 100000)
    key = FuzzyText(prefix='EX-', length=4, chars=string.digits)
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/latest/issue/{x.id}')
    fields = Dict({
        'assignee': SubFactory(AssigneeFactory),
        'status': SubFactory(StatusFactory),
        'summary': Faker('sentence'),
    })


class JiraResponseFactory(DictFactory):
    """A factory for a whole JIRA response."""

    maxResults = FuzzyInteger(100, 200)
    startAt = 0
    total = LazyAttribute(lambda x: len(x.issues))
    issues = List([JiraIssueFactory()])


class ReviewerFactory(DictFactory):
    """A factory for a reviewer in a pull request."""

    approved = FuzzyChoice([True, False])
    name = Faker('name')
    avatar = 'https://example.com?size=48&s=48'


class PullRequestFactory(DictFactory):
    """A factory for an pull request from BitBucket repos."""

    id = FuzzyInteger(1, 1000)
    name = FuzzyText(prefix='issue', length=3, chars=string.digits)
    reviewers = List([ReviewerFactory(), ReviewerFactory(), ReviewerFactory()])
    author = Dict({
        'avatar': 'https://example.com/128?size=48&s=48',
        'name': Faker('name'),
    })
    status = FuzzyChoice(['OPEN', 'DECLINED'])
    url = LazyAttribute(lambda x: f'https://bitbucket.org/example/example_repos/pull-requests/{x.id}')


class BitBucketIssueFactory(DictFactory):
    """A factory for a issue returned from the BitBucket api."""

    id = FuzzyInteger(10000, 100000)
    key = FuzzyText(prefix='EX-', length=4, chars=string.digits)
    pullRequests = List([PullRequestFactory()])
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/latest/issue/{x.id}')
    status = FuzzyChoice(['New', 'In Progress', 'In Review', 'Reviewed', 'To Deploy', 'Done'])
    title = Faker('sentence')


class BitBucketResponseFactory(DictFactory):
    """A factory for a whole BitBucket response."""

    detail = List([BitBucketIssueFactory()])
    errors = List([])


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
