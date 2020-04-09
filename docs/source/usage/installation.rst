Installation
============

Steps
-----

1. Download the github project

2. Set up the env variables:

- SLACK_CHANNEL_ID - the default channel ID to post to
- SLACK_TOKEN - your slack app token
- SLACK_SIGNING_SECRET - your slack app secret
- JIRA_EMAIL - your Jira email
- JIRA_TOKEN - your Jira token create via https://id.atlassian.com/manage/api-tokens
- JIRA_DOMAIN - your Jira domain (Note: add /rest/ at the end of the url so it connects to
  the Jira API.
- JIRA_SPRINT_NUMBER - your Jira sprint ID from with to gather data
- BROKER_URL - your broker url that will be used by Celery

3. Enable event subscription on your slack app

4. Set up the Request url for the event subscription

5. Run your broker and celery worker

6. Run the tornado app via:

.. code-block:: shell

    python manage.py
