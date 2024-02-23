from functools import wraps

from flask import abort, current_app, request

def enterprise_only(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if not current_app.config['ENTERPRISE']:
            abort(404)

        # get header 'X-Enterprise-Key'
        enterprise_key = request.headers.get('X-Enterprise-Key')
        if not enterprise_key or enterprise_key != current_app.config['ENTERPRISE_KEY']:
            abort(404)

        return view(*args, **kwargs)
    
    return decorated
