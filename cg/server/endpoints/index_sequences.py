from http import HTTPStatus

from flask import Blueprint, jsonify

from cg.server.endpoints.utils import before_request
from cg.services.orders.validation.index_sequences import INDEX_SEQUENCES

INDEX_SEQUENCES_BLUEPRINT = Blueprint("index_sequences", __name__, url_prefix="/api/v1")
INDEX_SEQUENCES_BLUEPRINT.before_request(before_request)


@INDEX_SEQUENCES_BLUEPRINT.route("index_sequences", methods=["GET"])
def get_index_sequences():
    return jsonify(INDEX_SEQUENCES), HTTPStatus.OK
