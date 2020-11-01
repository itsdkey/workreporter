=========
CHANGELOG
=========

0.0.7 (1.11.2020)
------------------

**Updates**

1. Code optimization and correcting code quality #24

2. Correcting bug while setting sprint number #23

0.0.6 (25.10.2020)
------------------

**Updates**

1. Added support for more then 50 blocks

0.0.5 (27.07.2020)
------------------

**Updates**

1. Added endpoint for storing sprint number in redis
    `/changesprint <int>`

0.0.4 (9.04.2020)
-----------------

**Updates**

1. Moved filtering pull requests to parsers. From now on the parser returns only
   pull requests that have reviewers that did not give an approval.

2. Changed the pull requests message title and ticket title.

3. Caching workspace users in Redis for performance. Also added a periodic task
   to update that list every 24hours.

0.0.3 (23.03.2020)
------------------

**Updates**

1. Added celery to make asynchronous work like periodic display messages.

2. Added documentation via sphinx.

0.0.2 (7.03.2020)
------------------

**Updates**

1. Added slugify for searching users that were not found so we can search again
   with ascii letters.

2. Changed plain_text type to mrkdwn in title section on empty pull requests newsletter.

0.0.1 (29.02.2020)
------------------

**Updates**

1. Runtime improvement thanks to anycio's coroutines.

* I've used aiohttp and aiodns for collecting Pull Requests from repos which resulted
  in an almost 4x faster execution when trying to retrieve multiple issues.

2. Added factories for API responses

0.0.0 (24.02.2020)
------------------

1. Working MVP (minimum value product)
