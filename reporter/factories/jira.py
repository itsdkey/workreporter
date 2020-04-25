import string
from uuid import uuid4

from factory import Dict, DictFactory, Faker, LazyAttribute, List, SubFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText


class AssigneeFactory(DictFactory):
    """
    A factory representing information about a user assigned to a given issue.
    This dictionary is a part of the JiraIssue dictionary returned by the JIRA API.
    """

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
    """
    A factory representing the status of an JIRA issue.
    This dictionary is a part of the JiraIssue dictionary returned by the JIRA API.
    """

    description = Faker('sentence')
    id = FuzzyInteger(10000, 100000)
    name = FuzzyChoice(['New', 'In Progress', 'In Review', 'Reviewed', 'To Deploy', 'Done'])
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/2/status/{x.id}')


class JiraIssueFactory(DictFactory):
    """A factory of an issue returned from the JIRA API."""

    id = FuzzyInteger(10000, 100000)
    key = FuzzyText(prefix='EX-', length=4, chars=string.digits)
    self = LazyAttribute(lambda x: f'https://example.com/rest/api/latest/issue/{x.id}')
    fields = Dict({
        'assignee': SubFactory(AssigneeFactory),
        'status': SubFactory(StatusFactory),
        'summary': Faker('sentence'),
    })


class JiraResponseFactory(DictFactory):
    """
    A factory for a whole JIRA response.
    This is the parsed JSON content returned by the JIRA API.
    """

    maxResults = FuzzyInteger(100, 200)
    startAt = 0
    total = LazyAttribute(lambda x: len(x.issues))
    issues = List([JiraIssueFactory()])
