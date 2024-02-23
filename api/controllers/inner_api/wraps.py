from functools import wraps

from flask import abort, current_app, request


def inner_api_only(view):
    @wraps(view)
    def decorated(*args, **kwargs):
        if not current_app.config['INNER_API']:
            abort(404)

        # get header 'X-Inner-Api-Key'
        inner_api_key = request.headers.get('X-Inner-Api-Key')
        if not inner_api_key or inner_api_key != current_app.config['INNER_API_KEY']:
            abort(404)

        return view(*args, **kwargs)
    
    return decorated
