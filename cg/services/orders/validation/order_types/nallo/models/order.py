from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.nallo.constants import NalloDeliveryType
from cg.services.orders.validation.order_types.nallo.models.case import NalloCase
from cg.services.orders.validation.order_types.nallo.models.sample import NalloSample

NewCase = Annotated[NalloCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class NalloOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: NalloDeliveryType

    @property
    def enumerated_new_samples(self) -> list[tuple[int, int, NalloSample]]:
        return [
            (case_index, sample_index, sample)
            for case_index, case in self.enumerated_new_cases
            for sample_index, sample in case.enumerated_new_samples
        ]
