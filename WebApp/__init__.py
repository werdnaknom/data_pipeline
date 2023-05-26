from flask import Flask, g, current_app
from config import Config

#from .extensions import mongo, bootstrap
#from .extensions import mongo

def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)
    print(app.config)
    #bootstrap.init_app(app)
    #mongo.init_app(app)

    ''' API '''
    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    print(config_class)

    return app