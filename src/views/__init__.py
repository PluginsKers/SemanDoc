from flask_restful import Api

from .upload_views import DocumentUploadResource
from .chat_views import ChatResource
from .documents_views import DocumentResource, DocumentsResource, DocumentsRecordsResource
from .users_views import UserResource
from .auth_views.login import LoginResource
from .wecom_views import WecomResource


def register_resources(api: Api):
    api.add_resource(DocumentResource, '/api/v1/document',
                     '/api/v1/document/<string:id>')

    api.add_resource(DocumentsResource, '/api/v1/documents')

    api.add_resource(DocumentsRecordsResource, '/api/v1/documents/records')

    api.add_resource(DocumentUploadResource, '/api/v1/upload/documents')

    api.add_resource(UserResource, '/api/v1/user',
                     '/api/v1/user/<int:id>')

    api.add_resource(WecomResource, '/api/v1/wecom')
    api.add_resource(LoginResource, '/api/v1/auth/login')

    api.add_resource(ChatResource, '/api/v1/chat')
