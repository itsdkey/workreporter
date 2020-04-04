class JiraParser:
    """A class responsible for parsing a JIRA API response."""

    @staticmethod
    def get_issues_with_state(state: str, issues_list: dict) -> list:
        """
        Return issues that have a specific state.

        :param state: a state name
        :param issues_list: issues from the API
        """
        issues = []
        for issue in issues_list['issues']:
            status = issue['fields']['status']['name']
            if status == state:
                info = {
                    'id': issue['id'],
                    'key': issue['key'],
                    'title': issue['fields']['summary'],
                    'status': status,
                    'self': issue['self'],
                }
                issues.append(info)
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
                        'title': detail['title'],
                        'pull_requests': assigned_pull_requests,
                    }
                    pull_requests.append(info)
        return pull_requests

    @staticmethod
    def _get_pull_requests_with_status(status: str, pull_requests: list) -> list:
        """
        Return a list of pull requests with a given status.

        :param status: status of pull requests that should be returned
        :param pull_requests: list of dictionaries that contain information
            about pull requests assigned to a ticket
        """
        opened_pull_requests = []
        for pull_request in pull_requests:
            if pull_request['status'] == status:
                info = {
                    'author': pull_request['author']['name'],
                    'url': pull_request['url'],
                    'reviewers': pull_request['reviewers'],
                }
                opened_pull_requests.append(info)
        return opened_pull_requests
