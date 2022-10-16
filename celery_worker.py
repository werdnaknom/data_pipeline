from app import create_app
from config import DevelopmentConfig, Config
from celery import Celery, group, chain
import numpy as np
import matplotlib.pyplot as plt


celeryapp = Celery('CeleryTasks',
                   broker='pyamqp://guest:guest@rabit:5672/vhost',
                   backend="redis://redis:6379/0")

celeryapp.autodiscover_tasks([__name__])
celeryapp.config_from_object("celeryconfig")  # celeryconfig.py

