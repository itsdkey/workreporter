from tornado.web import url

from .handlers import HomeHandler, SlackHandler

urls = [
    url(r'/', HomeHandler, name='main'),
    url(r'/slack/events/', SlackHandler, name='slack'),
]
