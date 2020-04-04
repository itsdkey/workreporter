"""
Server
======

The server package delivers modules that handle running an Tornado app.

handlers
--------

This module contains Tornado handlers. Handlers in Tornado can be compared to Views in Django. They are responsible
for handling requests send to the Tornado server and should be assigned to a given url.

.. automodule:: server.handlers
    :members:
    :show-inheritance:

tasks
-----

This module contains tasks that can be executed via Celery.

.. autofunction:: server.tasks.display_changelog

.. autofunction:: server.tasks.display_pull_requests

.. autofunction:: server.tasks.handle_message

"""
