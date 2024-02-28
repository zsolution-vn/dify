
from flask_restful import Resource, reqparse

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only
from services.conversation_service import ConversationService


class EnterpriseRenameApi(Resource):
    """Model invoke API for enterprise edition"""

    @setup_required
    @inner_api_only
    def post(self):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument("tenant_id", type=str, required=True, nullable=False, location="json")
        request_parser.add_argument("query", type=str, required=True, nullable=False, location="json")

        args = request_parser.parse_args()

        return ConversationService.auto_generate_name_string(
            tenant_id=args["tenant_id"], 
            query=args["query"]
        )

api.add_resource(EnterpriseRenameApi, "/service/rename")
