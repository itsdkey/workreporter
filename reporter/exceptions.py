class ResponseStatusCodeException(Exception):
    """
    An exception for wrong response status codes.

    It should be raised when the response's status code wasn't equal to an expected code.
    """

    pass
