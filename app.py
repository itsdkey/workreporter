import tornado.ioloop
from tornado.options import options, parse_command_line

from server.configuration.application import MyApplication
from server.urls import urls


def make_app() -> MyApplication:
    """Return a Tornado application."""
    app = MyApplication(urls)
    return app


def main():
    """Run the app."""
    parse_command_line()
    app = make_app()
    app.listen(options.port)
    print(f'Tornado app starting on port: {options.port}')
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print(f'Tornado app stoping on port: {options.port}')
        tornado.ioloop.IOLoop.current().stop()


if __name__ == '__main__':
    main()
