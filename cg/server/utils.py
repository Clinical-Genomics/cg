from requests import Request

from cg.server.dto.orders.orders_request import OrdersRequest


def parse_orders_request(request: Request) -> OrdersRequest:
    query_params: dict = request.args.to_dict()
    return OrdersRequest.model_validate(query_params)
