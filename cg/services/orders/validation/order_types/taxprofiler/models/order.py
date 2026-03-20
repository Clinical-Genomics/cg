from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.order_types.taxprofiler.constants import TaxprofilerDeliveryType
from cg.services.orders.validation.order_types.taxprofiler.models.sample import TaxprofilerSample


class TaxprofilerOrder(OrderWithSamples[TaxprofilerSample]):
    delivery_type: TaxprofilerDeliveryType
