import os

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()


broker_url = os.environ['BROKER_URL']

# List of modules to import when the Celery worker starts.
imports = ('server.tasks',)

enable_utc = True
timezone = 'Europe/Warsaw'

beat_schedule = {
    'display-changelog': {
        'task': 'server.tasks.display_changelog',
        'schedule': crontab(minute=0, hour='7', day_of_week='mon'),
        'args': None,
    },
    'display-pull-requests': {
        'task': 'server.tasks.display_pull_requests',
        'schedule': crontab(minute=0, hour='7,9,11,13,15', day_of_week='mon-fri'),
        'args': None,
    },
    'update-workspace-users': {
        'task': 'server.tasks.update_workspace_users',
        'schedule': crontab(minute=0, hour=0, day_of_week='mon-fri'),
        'args': None,
    },
}
