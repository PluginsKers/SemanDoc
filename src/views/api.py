# 导入Flask的Blueprint模块，用于创建蓝图
from flask import Blueprint

# 导入各个模块的蓝图
from src.views.routes.edit import editor_blueprint
from src.views.routes.query import query_blueprint

# 创建一个名为'api'的蓝图对象，__name__代表当前模块的名称
api_blueprint = Blueprint("api", __name__)

# 使用api_blueprint蓝图注册search模块的蓝图，设置其访问URL前缀为'/search'
api_blueprint.register_blueprint(query_blueprint, url_prefix="/query")

# 使用api_blueprint蓝图注册edit模块的蓝图，设置其访问URL前缀为'/edit'
api_blueprint.register_blueprint(editor_blueprint, url_prefix="/edit")
