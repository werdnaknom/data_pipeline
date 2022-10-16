import os


class Config(object):
    TESTING = False
    DEBUG = False
    '''
    DOCKER CONFIG FILES
    most configuration details exist in the .env file which is read when
    docker-compose goes "up".   Some configuration details can be checked using:
    "docker-compose config" from the file with the .yml file in it.
    '''
    # Database Config
    '''
    mongo_docker = os.environ.get('MONGO_DOCKER_NAME')
    mongo_db = os.environ.get("DB_NAME")
    mongo_port = os.environ.get('MONGO_PORT')
    MONGO_URI = "mongodb://{mongo_docker}:{mongo_port}/{mongo_db}".format(
        mongo_docker=mongo_docker, mongo_port=mongo_port, mongo_db=mongo_db)
    '''
    # Defined in .env  file
    MONGO_URI = os.environ.get("MONGO_URI")

    # Redis Config
    redis_docker = os.environ.get("REDIS_DOCKER_NAME")
    # redis_port = os.environ.get("REDIS_PORT")
    # TODO:: Correct redis URL.. if redis is used?
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    RESULTS_FOLDER = os.environ.get("RESULTS_FOLDER")
    CELERY_TEMP_FOLDER = os.environ.get("CELERY_TEMP_FOLDER")

    # Celery Config
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
    '''
    CELERY_RESULT_BACKEND = 'redis://{redis_docker}:{redis_port}/0'.format(
        redis_docker=redis_docker, redis_port=redis_port)
    celery_user = os.environ.get("CELERY_USER")
    celery_password = os.environ.get("CELERY_PASSWORD")
    celery_host = os.environ.get("CELERY_HOST")
    celery_docker = os.environ.get("CELERY_DOCKER")
    celery_port = os.environ.get("CELERY_PORT")
    CELERY_BROKER_URL = 'amqp://{celery_user}:{celery_password}@' \
                        '{celery_docker}:{celery_port}/{celery_host}'.format(
        celery_user=celery_user,
        celery_docker=celery_docker,
        celery_password=celery_password,
        celery_port=celery_port,
        celery_host=celery_host,
    )

    #CELERY_BROKER_URL = 'amqp://guest:guest@rabbit:5672/vhost'
    '''

    CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
    CELERY_ROUTES = {
        'post_processor': {
            'exchange': 'worker',  # -Q name during run command
            'exchange_type': 'direct',
            'routing_key': 'worker'  # -Q name during run command
        },
        'waveform_reader_subtract': {
            'exchange': 'worker',  # -Q name during run command
            'exchange_type': 'direct',
            'routing_key': 'worker'  # -Q name during run command
        },
        'single_waveform': {
            'exchange': 'worker',  # -Q name during run command
            'exchange_type': 'direct',
            'routing_key': 'worker'  # -Q name during run command
        },
        'group_waveform': {
            'exchange': 'worker',  # -Q name during run command
            'exchange_type': 'direct',
            'routing_key': 'worker'  # -Q name during run command
        }
    }
    # MISC CONFIGS
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super secret key"
    # LOGGING CONFIG
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
    # BABEL Config
    LANGUAGES = {
        "en": "English",
    }


class DockerConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = True

    '''
    # Database Config
    '''
    MONGO_URI = "mongodb://localhost:27017"
    REDIS_URL = 'redis://localhost'

    UPLOAD_FOLDER = r"C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads"
    RESULTS_FOLDER = r"C:\Users\ammonk\OneDrive - Intel Corporation\Desktop\Test_Folder\fake_uploads\fake_results"
    CELERY_TEMP_FOLDER = r"C:/Users/ammonk/OneDrive - Intel " \
                         r"Corporation/Desktop/Test_Folder/fake_uploads" \
                         r"/CeleryTemp"

    # Celery Config
    CELERY_BROKER_URL = "pyamqp://guest:guest@localhost:5672/vhost"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"


class TestingConfig(Config):
    TESTING = True
