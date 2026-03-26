from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.pacbio_long_read.constants import PacbioDeliveryType
from cg.services.orders.validation.order_types.pacbio_long_read.models.sample import PacbioSample


class PacbioOrder(OrderWithSamples[PacbioSample]):
    delivery_type: PacbioDeliveryType
