from flask_restful import Resource, reqparse


class AuthResource(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser(bundle_errors=True)
        super(AuthResource, self).__init__()
