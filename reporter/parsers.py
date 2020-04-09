class JiraParser:
    """A class responsible for parsing a JIRA API response."""

    @staticmethod
    def filter_out_important_data(issues_list: dict) -> list:
        """
        Flatter the dictionary to only important information.

        :param issues_list: issues from the API
        """
        issues = [
            {
                'id': issue['id'],
                'key': issue['key'],
                'title': issue['fields']['summary'],
                'status': issue['fields']['status']['name'],
                'self': issue['self'],
            } for issue in issues_list['issues']
        ]
        return issues

    def parse_pull_request_info(self, tickets_info_response: list) -> list:
        """
        Return only necessary info about pull request.

        :param tickets_info_response: a list of dictionaries that contains
            information about tickets in a sprint board.
        """
        pull_requests = []
        for ticket in tickets_info_response:
            for detail in ticket['detail']:
                assigned_pull_requests = self._get_pull_requests_with_status(
                    'OPEN',
                    detail['pullRequests'],
                )
                if assigned_pull_requests:
                    info = {
                        'key': detail['key'],
                        'title': detail['title'],
                        'pull_requests': assigned_pull_requests,
                    }
                    pull_requests.append(info)
        return pull_requests

    @staticmethod
    def _get_pull_requests_with_status(status: str, pull_requests: list) -> list:
        """
        Return a list of pull requests with a given status.

        Only pull requests which have assigned reviewers that did not give an approval are returned.

        :param status: status of pull requests that should be returned
        :param pull_requests: list of dictionaries that contain information
            about pull requests assigned to a ticket
        """
        opened_pull_requests = []
        for pull_request in pull_requests:
            if pull_request['status'] == status:
                reviewers = list(filter(lambda x: not x['approved'], pull_request['reviewers']))
                if reviewers:
                    info = {
                        'author': pull_request['author']['name'],
                        'url': pull_request['url'],
                        'reviewers': [x['name'] for x in reviewers],
                    }
                    opened_pull_requests.append(info)
        return opened_pull_requests
