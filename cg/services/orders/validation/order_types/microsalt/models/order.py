from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.microsalt.constants import MicrosaltDeliveryType
from cg.services.orders.validation.order_types.microsalt.models.sample import MicrosaltSample


class MicrosaltOrder(OrderWithSamples[MicrosaltSample]):
    delivery_type: MicrosaltDeliveryType
