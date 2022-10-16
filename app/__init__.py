from celery import Celery
from config import Config, DevelopmentConfig
import sys

if sys.platform == "win32":
    globalConfig = DevelopmentConfig()
else:
    globalConfig = Config()

"""
def init_celery():
    ''' Add flaskapp context to celery.Task'''
    celeryapp = Celery('web',
                       broker='pyamqp://guest:guest@localhost:5672/vhost',
                       backend="redis://localhost:6379/0")
    celeryapp.conf.update(app.config)

    class ContextTask(celeryapp.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                self.run(*args, **kwargs)

    celeryapp.Task = ContextTask
    return celeryapp
"""


def create_app(config_class=Config):
    # Configure Celery
    # celeryapp = init_celery(flask_app)
    celeryapp = Celery('web',
                       broker='pyamqp://guest:guest@localhost:5672/vhost',
                       backend="redis://localhost:6379/0")
    celeryapp.config_from_object(config_class)

    return celeryapp
