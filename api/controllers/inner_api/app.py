import json
import logging
from flask_login import current_user
from flask_restful import Resource, reqparse
from flask import Response
from flask.helpers import stream_with_context

from controllers.console.setup import setup_required
from controllers.inner_api import api
from controllers.inner_api.wraps import inner_api_only, inner_api_user_auth
from services.completion_service import CompletionService
from core.entities.application_entities import InvokeFrom

from extensions.ext_database import db
from models.model import App, EndUser

from typing import Union, Generator
from werkzeug.exceptions import InternalServerError, NotFound

import services
from controllers.service_api.app.error import (
    AppUnavailableError,
    CompletionRequestError,
    ConversationCompletedError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from core.entities.application_entities import InvokeFrom
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.model_runtime.errors.invoke import InvokeError

class EnterpriseAppInvokeApi(Resource):
    """App invoke API for enterprise edition"""

    @setup_required
    @inner_api_only
    @inner_api_user_auth
    def post(self, **kwargs: dict):
        request_parser = reqparse.RequestParser()
        request_parser.add_argument('app_id', type=str, required=True, nullable=False, location='json')
        request_parser.add_argument('query', type=str, required=True, nullable=False, location='json')
        request_parser.add_argument('inputs', type=dict, required=True, nullable=False, location='json')
        request_parser.add_argument('stream', type=bool, required=False, nullable=False, location='json')
        request_parser.add_argument('conversation_id', type=str, required=False, nullable=True, location='json')

        args = request_parser.parse_args()

        try:
            app_id = args['app_id']
            app_model: App = db.session.query(App).filter(App.id == app_id).first()
            if app_model is None:
                raise NotFound("App Not Exists.")
            
            # disable auto generate name
            args['auto_generate_name'] = False
            
            response = CompletionService.completion(
                app_model=app_model,
                user=kwargs['user'] if 'user' in kwargs else current_user,
                args=args,
                invoke_from=InvokeFrom.INNER_API,
                streaming=args['stream'] if 'stream' in args else False,
            )

            return compact_response(response)
        except services.errors.conversation.ConversationNotExistsError:
            raise NotFound("Conversation Not Exists.")
        except services.errors.conversation.ConversationCompletedError:
            raise ConversationCompletedError()
        except services.errors.app_model_config.AppModelConfigBrokenError:
            logging.exception("App model config broken.")
            raise AppUnavailableError()
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
            logging.exception("internal server error.")
            raise InternalServerError()


def compact_response(response: Union[dict, Generator]) -> Response:
    if isinstance(response, dict):
        return Response(response=json.dumps(response), status=200, mimetype='application/json')
    else:
        def generate() -> Generator:
            yield from response

        return Response(stream_with_context(generate()), status=200,
                        mimetype='text/event-stream')    

api.add_resource(EnterpriseAppInvokeApi, '/app/invoke')