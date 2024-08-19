from cg.models.orders.samples import MicrosaltSample
from cg.services.order_validation_service.models.order import Order


class MicroSaltOrder(Order):
    samples: list[MicrosaltSample]
