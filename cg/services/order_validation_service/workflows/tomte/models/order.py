from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


class TomteOrder(Order):
    cases: list[TomteCase]
