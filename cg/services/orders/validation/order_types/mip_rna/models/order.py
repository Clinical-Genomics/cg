from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.mip_rna.constants import MIPRNADeliveryType
from cg.services.orders.validation.order_types.mip_rna.models.case import MIPRNACase

NewCase = Annotated[MIPRNACase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class MIPRNAOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: MIPRNADeliveryType
