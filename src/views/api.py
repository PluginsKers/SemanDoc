from flask import Blueprint
from src.views.routes.edit import editor_blueprint
from src.views.routes.support import support_blueprint
from src.views.routes.query import query_blueprint

api_blueprint = Blueprint('api', __name__)

# 注册接口内容
api_blueprint.register_blueprint(
    query_blueprint,
    url_prefix='/query'
)

api_blueprint.register_blueprint(
    support_blueprint,
    url_prefix='/support'
)

api_blueprint.register_blueprint(
    editor_blueprint,
    url_prefix='/edit'
)
