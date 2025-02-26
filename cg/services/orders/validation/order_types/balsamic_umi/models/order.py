from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic_umi.constants import BalsamicUmiDeliveryType
from cg.services.orders.validation.order_types.balsamic_umi.models.case import BalsamicUmiCase

NewCase = Annotated[BalsamicUmiCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class BalsamicUmiOrder(BalsamicOrder):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: BalsamicUmiDeliveryType

    @property
    def enumerated_new_cases(self) -> list[tuple[int, BalsamicUmiCase | ExistingCase]]:
        cases: list[tuple[int, BalsamicUmiCase | ExistingCase]] = []
        for case_index, case in self.enumerated_cases:
            if case.is_new:
                cases.append((case_index, case))
        return cases
