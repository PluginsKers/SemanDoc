from flask import Blueprint

from src.views.routes.edit import editor_blueprint
from src.views.routes.query import query_blueprint
from src.views.routes.wecom import wecom_blueprint

api_blueprint = Blueprint("api", __name__)

api_blueprint.register_blueprint(query_blueprint, url_prefix="/query")
api_blueprint.register_blueprint(editor_blueprint, url_prefix="/edit")
api_blueprint.register_blueprint(wecom_blueprint, url_prefix="/wecom")
