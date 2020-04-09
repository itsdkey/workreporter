=========
CHANGELOG
=========

0.0.4 (9.04.2020)
-----------------

**Updates**

1. Moved filtering pull requests to parsers. From now on the parser returns only
pull requests that have reviewers that did not give an approval.

2. Changed the pull requests message title and ticket title.


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
