from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.balsamic_umi.constants import (
    BalsamicUmiDeliveryType,
)
from cg.services.order_validation_service.workflows.balsamic_umi.models.case import BalsamicUmiCase

NewCase = Annotated[BalsamicUmiCase, Tag("new")]
OldCase = Annotated[ExistingCase, Tag("existing")]


class BalsamicUmiOrder(BalsamicOrder):
    cases: list[Annotated[NewCase | OldCase, Discriminator(has_internal_id)]]
    delivery_type: BalsamicUmiDeliveryType
