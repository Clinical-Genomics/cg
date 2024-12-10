from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.discriminators import has_internal_id
from cg.services.order_validation_service.models.existing_sample import ExistingSample
from cg.services.order_validation_service.workflows.mip_rna.models.sample import (
    MipRnaSample,
)

NewSample = Annotated[MipRnaSample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class MipRnaCase(Case):
    cohorts: list[str] | None = None
    synopsis: str | None = None
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]
