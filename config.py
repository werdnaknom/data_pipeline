import os

from dotenv import load_dotenv

load_dotenv()

import logging

logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


class Config():
    DEBUG = True
    TEST = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "this_key_is_secret_1987"
    ENVIRONMENT = os.environ.get("ENVIRONMENT") or "DEVELOPMENT"
    REPOSITORY_URL = os.environ.get("REPOSITORY_URL") or "http://127.0.0.1:5001"