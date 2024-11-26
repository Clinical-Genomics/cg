from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.tomte.constants import TomteDeliveryType
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase

NewCase = Annotated[TomteCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class TomteOrder(OrderWithCases):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: TomteDeliveryType
