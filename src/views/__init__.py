from flask_restful import Api
from .document_views import DocumentResource
from .user_views import UserResource
from .auth_views.login import LoginResource
from .wecom_views import WecomResource


def register_resources(api: Api):
    api.add_resource(DocumentResource, '/api/v1/documents',
                     '/api/v1/documents/<string:id>')
    api.add_resource(UserResource, '/api/v1/users',
                     '/api/v1/users/<string:id>')

    api.add_resource(WecomResource, '/api/v1/wecom')
    api.add_resource(LoginResource, '/api/v1/auth/login')
