import json

from flask_restful import Resource, reqparse
from flask import Response
from flask.helpers import stream_with_context

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only

from services.completion_service import CompletionService

from typing import Generator, Union

class EnterpriseModelInvokeLLMApi(Resource):
    """Model invoke API for enterprise edition"""

    @setup_required
    @inner_api_only
    def post(self):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument('tenant_id', type=str, required=True, nullable=False, location='json')
        request_parser.add_argument('provider', type=str, required=True, nullable=False, location='json')
        request_parser.add_argument('model', type=str, required=True, nullable=False, location='json')
        request_parser.add_argument('completion_params', type=dict, required=True, nullable=False, location='json')
        request_parser.add_argument('prompt_messages', type=list, required=True, nullable=False, location='json')
        request_parser.add_argument('tools', type=list, required=False, nullable=True, location='json')
        request_parser.add_argument('stop', type=list, required=False, nullable=True, location='json')
        request_parser.add_argument('stream', type=bool, required=False, nullable=True, location='json')
        request_parser.add_argument('user', type=str, required=False, nullable=True, location='json')

        args = request_parser.parse_args()

        response = CompletionService.invoke_model(
            tenant_id=args['tenant_id'],
            provider=args['provider'],
            model=args['model'],
            completion_params=args['completion_params'],
            prompt_messages=args['prompt_messages'],
            tools=args['tools'],
            stop=args['stop'],
            stream=args['stream'],
            user=args['user'],
        )

        return compact_response(response)

def compact_response(response: Union[dict, Generator]) -> Response:
    if isinstance(response, dict):
        return Response(response=json.dumps(response), status=200, mimetype='application/json')
    else:
        def generate() -> Generator:
            yield from response

        return Response(stream_with_context(generate()), status=200,
                        mimetype='text/event-stream')    

api.add_resource(EnterpriseModelInvokeLLMApi, '/model/invoke/llm')
