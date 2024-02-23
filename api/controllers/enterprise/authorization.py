from flask_login import current_user

from controllers.enterprise import api
from controllers.console.setup import setup_required
from libs.login import login_required
from controllers.enterprise.wraps import enterprise_only
from flask_restful import Resource

class EnterpriseAuthorizationApi(Resource):
    """Authorization API for enterprise edition, share user and tenant info."""

    @setup_required
    @login_required
    @enterprise_only
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
            'current_tenant_role': current_tenant.current_role
        }
    
api.add_resource(EnterpriseAuthorizationApi, '/authorization/info')