from tornado.web import url

from .handlers import HomeHandler, SlackHandler, SprintChangeHandler

urls = [
    url(r'/', HomeHandler, name='main'),
    url(r'/slack/events/', SlackHandler, name='slack'),
    url(r'/sprint/change/', SprintChangeHandler, name='sprint-change'),
]
