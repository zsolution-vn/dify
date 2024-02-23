from flask import Blueprint
from libs.external_api import ExternalApi

bp = Blueprint('enterprise', __name__, url_prefix='/enterprise/api')
api = ExternalApi(bp)

from . import authorization