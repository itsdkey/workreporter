Work reporter
===========================

A simple BB, JIRA and slack integration.

One of it's main purposes is to collect issues in review and inform your colleagues
about requested reviews via slack.


Install the requirements
------------------------

Note: This projects runs under Python 3.7

.. code-block:: shell

    pip install -r requirements.txt

Create the docs
---------------

.. code-block:: shell

    make html

The docs will be created under build folder. Read it for further installation info.


Run tests
---------

.. code-block:: shell

    python -m unittest
