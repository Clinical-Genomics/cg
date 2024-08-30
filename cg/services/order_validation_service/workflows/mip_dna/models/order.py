from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.mip_dna.models.case import (
    MipDnaCase,
)

NewCase = Annotated[MipDnaCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class MipDnaOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
