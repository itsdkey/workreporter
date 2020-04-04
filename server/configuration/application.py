from tornado.web import Application

from .settings import settings


class MyApplication(Application):
    """A Tornado application."""

    def __init__(self, urls):
        super().__init__(urls, **settings)
