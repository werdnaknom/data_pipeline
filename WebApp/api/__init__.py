from flask import Blueprint

bp = Blueprint('api', __name__)

from WebApp.api import routes