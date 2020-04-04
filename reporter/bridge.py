from .apps import JiraApp, SlackApp


class Bridge:
    """Class for representing a bridge between Jira and Slack."""

    def __init__(self, sprint_number=None, **kwargs):
        """
        Initialize.

        :param sprint_number: a number of the sprint to search
        """
        self.jira = JiraApp(sprint_number, **kwargs)
        self.slack = SlackApp(channel_id=kwargs.get('channel_id'), loop=kwargs.get('loop'))

    async def run(self) -> None:
        """Gather data from Jira and post it to slack."""
        pull_requests = await self.jira.run()
        if pull_requests:
            await self.slack.remind_about_pull_requests(pull_requests)
        else:
            await self.slack.send_no_pull_requests_message()
