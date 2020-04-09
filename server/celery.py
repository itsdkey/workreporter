from celery import Celery

app = Celery('server')
app.config_from_object('server.configuration.celeryconfig')


if __name__ == '__main__':
    app.start()
