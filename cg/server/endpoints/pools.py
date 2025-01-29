from http import HTTPStatus

from flask import Blueprint, abort, g, jsonify, request

from cg.server.dto.pools.requests import PoolsRequest
from cg.server.endpoints.utils import before_request
from cg.server.ext import db
from cg.store.models import Customer, Pool

POOLS_BLUEPRINT = Blueprint("pools", __name__, url_prefix="/api/v1")
POOLS_BLUEPRINT.before_request(before_request)


@POOLS_BLUEPRINT.route("/pools")
def parse_pools():
    """Return pools."""
    pools_request = PoolsRequest.model_validate(request.args.to_dict())
    customers: list[Customer] | None = (
        g.current_user.customers if not g.current_user.is_admin else None
    )
    pools, total = db.get_pools_to_render(
        customers=customers,
        enquiry=pools_request.enquiry,
        limit=pools_request.page_size,
        offset=(pools_request.page - 1) * pools_request.page_size,
    )
    parsed_pools: list[dict] = [pool_obj.to_dict() for pool_obj in pools]
    return jsonify(pools=parsed_pools, total=total)


@POOLS_BLUEPRINT.route("/pools/<pool_id>")
def parse_pool(pool_id):
    """Return a single pool."""
    pool: Pool = db.get_pool_by_entry_id(entry_id=pool_id)
    if pool is None:
        return abort(HTTPStatus.NOT_FOUND)
    if not g.current_user.is_admin and (pool.customer not in g.current_user.customers):
        return abort(HTTPStatus.FORBIDDEN)
    return jsonify(**pool.to_dict())
