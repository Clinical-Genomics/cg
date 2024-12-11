from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.workflows.balsamic.models.case import BalsamicCase
from cg.services.order_validation_service.workflows.balsamic_umi.models.sample import (
    BalsamicUmiSample,
)

NewSample = Annotated[BalsamicUmiSample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class BalsamicUmiCase(BalsamicCase):
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]
