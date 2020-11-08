import os

# Slack credentials
SLACK_CHANNEL_ID = os.environ.get('SLACK_CHANNEL_ID', '')
SLACK_TOKEN = os.environ['SLACK_TOKEN']


# JIRA credentials
JIRA_AUTH = (os.environ['JIRA_EMAIL'], os.environ['JIRA_TOKEN'])
JIRA_DOMAIN = os.environ['JIRA_DOMAIN']
JIRA_SPRINT = os.environ.get('JIRA_SPRINT_NUMBER', '')
