import os

from tornado.options import define

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

define('port', default=8000, type=int)

settings = {
    'static_path': '',
    'template_path': '',
    'debug': True,
    'cookie_secret': str(os.urandom(45)),
    'xsrf_cookies': False,  # umożliwia wykonywanie POST na formularzach
    'gzip': True,  # umożliwia przesyłanie skomprezowanych wartości
}

secure_pages = []

SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']

REDIS_SOCKET_PATH = os.environ.get('REDIS_SOCKET_PATH', None)
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
REDIS_DATABASE = os.environ.get('REDIS_DATABASE', 0)
REDIS_HOST = os.environ['REDIS_HOST']
