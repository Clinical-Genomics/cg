from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.workflows.rna_fusion.constants import RnaFusionDeliveryType
from cg.services.orders.validation.workflows.rna_fusion.models.case import RnaFusionCase

NewCase = Annotated[RnaFusionCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class RnaFusionOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: RnaFusionDeliveryType
