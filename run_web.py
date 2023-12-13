from flask import Flask, jsonify, request
from config import Config
from WebApp import create_app

app = create_app(config_class=Config)

if __name__ == '__main__':

    environment = app.config.get("ENVIRONMENT")
    if environment == "PRODUCTION":
        from multiprocessing import cpu_count
        from gunicorn.app.base import BaseApplication


        class GunicornApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application


        workers = cpu_count() * 2 + 1
        options = {
            'bind': '0.0.0.0:5000',
            'workers': workers,
            'worker_class': 'gevent'
        }

        GunicornApplication(app, options).run()
    elif environment == "DEVELOPMENT":
        app.run(debug=True, port=5002)
    else:
        print(environment)

