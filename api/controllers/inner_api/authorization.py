from flask_login import current_user
from flask_restful import Resource

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only


class EnterpriseAuthorizationApi(Resource):
    """Authorization API for inner_api edition, share user and tenant info."""

    @setup_required
    @inner_api_only
    def get(self):
        current_tenant = current_user.current_tenant
        return {
            'id': current_user.id,
            'name': current_user.name,
            'avatar': current_user.avatar,
            'current_tenant' : {
                'id': current_tenant.id,
                'name': current_tenant.name,
                'plan': current_tenant.plan,
            },
            'current_tenant_role': current_tenant.current_role,
            'timezone': current_user.timezone,
        }
    
api.add_resource(EnterpriseAuthorizationApi, '/authorization/info')