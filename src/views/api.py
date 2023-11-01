from flask import Blueprint
from src.views.routes.edit import editor_blue
from src.views.routes.support import support_blue
from src.views.routes.query import query_blue

api_blue = Blueprint('api', __name__)


api_blue.register_blueprint(
    query_blue,
    url_prefix='/query'
)

api_blue.register_blueprint(
    support_blue,
    url_prefix='/support'
)

api_blue.register_blueprint(
    editor_blue,
    url_prefix='/edit'
)
