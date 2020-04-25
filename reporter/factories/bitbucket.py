import string

from factory import Dict, DictFactory, Faker, LazyAttribute, List
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText


class ReviewerFactory(DictFactory):
    """
    A factory representing a reviewer in a pull request.
    This dictionary is a part of the PullRequest dictionary returned by the BitBucket API.
    """

    approved = FuzzyChoice([True, False])
    name = Faker('name')
    avatar = 'https://example.com?size=48&s=48'


class PullRequestFactory(DictFactory):
    """
    A factory representing a pull request.
    This dictionary is a part of the BitBucketIssue dictionary returned from the BitBucket API.
    This dictionary is also a trimmed response, it contains only important information for us.
    A real BitBucket pull request response contains:
    {
        'author': { information about the PR author },
        'commentCount': an integer representing the number of comments in the review,
        'destination': { information about the target branch },
        'id': an identifier of the review,
        'lastUpdate': datetime in isoformat,
        'name': the name of the pull request,
        'reviewers': [ a list of dictionaries that contain information who is assigned to review this PR ],
        'source': { information about the source branch },
        'status': the status of the review,
        'url': the review URL,
    }
    """

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
    """
    A factory representing an issue returned from the BitBucket API.
    This dictionary is a trimmed response, it only has information that are important for us.
    A real BitBucket API response contains:
    {
        _instance: { information about the Bitbucket instance },
        branches: [ a list of dictionaries that contain information about created branches connected to this issue ],
        pullRequests: [ a list of dictionaries that contain information about reviews connected to this issue ],
        repositories: [ ],
    }
    """

    pullRequests = List([PullRequestFactory()])


class BitBucketResponseFactory(DictFactory):
    """
    A factory for a whole BitBucket response.
    This is the parsed JSON content returned by the BitBucket API.
    """

    detail = List([BitBucketIssueFactory()])
    errors = List([])
