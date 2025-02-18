from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.mip_rna.models.sample import MIPRNASample

NewSample = Annotated[MIPRNASample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class MIPRNACase(Case):
    cohorts: list[str] | None = None
    synopsis: str | None = None
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]
