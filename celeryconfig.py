import os

CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND") or "redis://redis:6379/0"
CELERY_BROKER_URL = os.environ.get(
    "CELERY_BROKER_URL") or 'pyamqp://guest:guest@rabbit:5672/vhost'

CELERY_IMPORTS = ('app.CeleryTasks')
