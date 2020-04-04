"""
Spammer
=======

Spammer package contains the whole logic responsible for collecting data from Jira and Bitbucket and sending it to
slack.


Adapters
--------

This module contains adapters that are responsible for connecting to REST APIs delivered by 3rd party products such
as Jira, BitBucket and Slack. Adapters connect to a given API and parse their response to a useful python object that
can be used in the application.

.. automodule:: reporter.adapters
    :members:
    :show-inheritance:


Apps
----

This module contains apps that are a top layer for adapters. Apps contain logic related to a 3rd party like Jira,
for example a Jira app should contain logic that will gather data from a sprint board.

.. automodule:: reporter.apps
    :members:
    :show-inheritance:


Bridge
------

This module contains a class that glues the whole reporter together. It connects the Jira app with the Slack one so we
can post messages of the gathered data.

.. automodule:: reporter.bridge
    :members:
    :show-inheritance:


Exceptions
----------

This module contains custom exceptions that are used by the reporter package.

.. automodule:: reporter.exceptions
    :members:
    :show-inheritance:


Parsers
-------

This module contains parsers that are responsible for modifying data collected from adapters. A parser should contain
logic that restructures or filters data returned from an adapter.

.. automodule:: reporter.parsers
    :members:
    :show-inheritance:

"""
