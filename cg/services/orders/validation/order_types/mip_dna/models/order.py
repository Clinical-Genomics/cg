from typing import cast

from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.mip_dna.constants import MIPDNADeliveryType
from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase

NewCase = Annotated[MIPDNACase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class MIPDNAOrder(OrderWithCases[MIPDNACase]):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: MIPDNADeliveryType

    @property
    def enumerated_new_cases(self) -> list[tuple[int, MIPDNACase]]:
        cases: list[tuple[int, MIPDNACase]] = []
        for case_index, case in self.enumerated_cases:
            if isinstance(case, MIPDNACase):
                cases.append((case_index, case))
        return cases
