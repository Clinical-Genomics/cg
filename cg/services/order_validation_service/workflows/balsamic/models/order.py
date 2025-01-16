from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.balsamic.constants import BalsamicDeliveryType
from cg.services.order_validation_service.workflows.balsamic.models.case import BalsamicCase

NewCase = Annotated[BalsamicCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class BalsamicOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: BalsamicDeliveryType

    @property
    def enumerated_new_cases(self) -> list[tuple[int, BalsamicCase | ExistingCase]]:
        cases: list[tuple[int, BalsamicCase | ExistingCase]] = []
        for case_index, case in self.enumerated_cases:
            if case.is_new:
                cases.append((case_index, case))
        return cases
