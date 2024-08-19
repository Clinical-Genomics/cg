from cg.models.orders.samples import MicrosaltSample
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.microsalt.constants import (
    MicrosaltDeliveryType,
)


class MicroSaltOrder(Order):
    delivery_type: MicrosaltDeliveryType
    samples: list[MicrosaltSample]
