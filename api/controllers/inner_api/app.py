from flask_login import current_user
from flask_restful import Resource

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only


class EnterpriseAppInvokeApi(Resource):
    """App invoke API for enterprise edition"""

    @setup_required
    @inner_api_only
    def post(self):
        pass
    
api.add_resource(EnterpriseAppInvokeApi, '/app/invoke')