Work reporter
===========================

A simple BB, JIRA and slack integration.

One of it's main purposes is to collect issues in review and inform your colleagues
about requested reviews via slack.


Requirements
------------

This project requires Redis

Download the docker image
-------------------------

Note: This projects runs under Python 3.9

.. code-block:: shell

    docker pull itsdkey/workreporter

Set up your docker-compose file
-------------------------------

.. code-block:: yaml

 version: "3.8"

 services:
     workreporter:
        environment:
            SLACK_CHANNEL_ID: <your channel id where to post to>
            SLACK_TOKEN: <your slack app token>
            SLACK_SIGNING_SECRET: <your slack signing secret>
            JIRA_EMAIL: <your jira account's email>
            JIRA_TOKEN: <your jira token>
            JIRA_DOMAIN: <your jira domain>
            JIRA_SPRINT_NUMBER: <your initial sprint number - you can change it with /changesprint command>
            BROKER_URL: <your broker url>
            REDIS_DATABASE: <your redis database>
            REDIS_HOST: <your redis host>
        ports:
            - <your outside port>:8888
     redis:
        image: redis:latest
        ports:
        - "6379:6379"

Run tests
---------

Inside a docker container in /workreporter run:

.. code-block:: shell

    python -m unittest

Dev tools
---------

Create the docs
---------------

.. code-block:: shell

    make html

The docs will be created under build folder. Read it for further installation info.
