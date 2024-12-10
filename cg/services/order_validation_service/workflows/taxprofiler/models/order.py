from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.workflows.taxprofiler.constants import (
    TaxprofilerDeliveryType,
)
from cg.services.order_validation_service.workflows.taxprofiler.models.sample import (
    TaxprofilerSample,
)


class TaxprofilerOrder(OrderWithSamples):
    delivery_type: TaxprofilerDeliveryType
    samples: list[TaxprofilerSample]

    @property
    def enumerated_samples(self) -> enumerate[TaxprofilerSample]:
        return enumerate(self.samples)
