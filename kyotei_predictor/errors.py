
from flask import jsonify

class APIError(Exception):
    """APIエラーのベースクラス"""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

def register_error_handlers(app):
    """Flaskアプリにエラーハンドラーを登録"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        response = jsonify({
            'message': 'Resource not found',
            'status_code': 404
        })
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def handle_server_error(error):
        response = jsonify({
            'message': 'Internal server error',
            'status_code': 500
        })
        response.status_code = 500
        return response
