import json
from collections.abc import Generator
from typing import Union

from flask import Response
from flask.helpers import stream_with_context
from flask_restful import Resource, reqparse
from werkzeug.exceptions import InternalServerError

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only
from controllers.service_api.app.error import (
    CompletionRequestError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.model_runtime.errors.invoke import InvokeError
from services.completion_service import CompletionService


class EnterpriseModelInvokeLLMApi(Resource):
    """Model invoke API for enterprise edition"""

    @setup_required
    @inner_api_only
    def post(self):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument("tenant_id", type=str, required=True, nullable=False, location="json")
        request_parser.add_argument("provider", type=str, required=True, nullable=False, location="json")
        request_parser.add_argument("model", type=str, required=True, nullable=False, location="json")
        request_parser.add_argument("completion_params", type=dict, required=False, nullable=False, location="json")
        request_parser.add_argument("prompt_messages", type=list, required=True, nullable=False, location="json")
        request_parser.add_argument("tools", type=list, required=False, nullable=True, location="json")
        request_parser.add_argument("stop", type=list, required=False, nullable=True, location="json")
        request_parser.add_argument("stream", type=bool, required=False, nullable=True, location="json")
        request_parser.add_argument("user", type=str, required=False, nullable=True, location="json")

        args = request_parser.parse_args()

        try:
            response = CompletionService.invoke_model(
                tenant_id=args["tenant_id"],
                provider=args["provider"],
                model=args["model"],
                completion_params=args["completion_params"],
                prompt_messages=args["prompt_messages"],
                tools=args["tools"],
                stop=args["stop"],
                stream=args["stream"],
                user=args["user"],
            )

            return compact_response(response)
        except ProviderTokenNotInitError as ex:
            raise ProviderNotInitializeError(ex.description)
        except QuotaExceededError:
            raise ProviderQuotaExceededError()
        except ModelCurrentlyNotSupportError:
            raise ProviderModelCurrentlyNotSupportError()
        except InvokeError as e:
            raise CompletionRequestError(e.description)
        except ValueError as e:
            raise e
        except Exception as e:
            raise InternalServerError()


def compact_response(response: Union[dict, Generator]) -> Response:
    if isinstance(response, dict):
        return Response(response=json.dumps(response), status=200, mimetype="application/json")
    else:

        def generate() -> Generator:
            yield from response

        return Response(stream_with_context(generate()), status=200, mimetype="text/event-stream")


api.add_resource(EnterpriseModelInvokeLLMApi, "/model/invoke/llm")
