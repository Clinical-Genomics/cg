from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.tomte.constants import (
    TomteDeliveryType,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


class TomteOrder(OrderWithCases):
    cases: list[
        Annotated[
            Annotated[TomteCase, Tag("new")] | Annotated[ExistingCase, Tag("existing")],
            Discriminator(has_internal_id),
        ]
    ]
    delivery_type: TomteDeliveryType
