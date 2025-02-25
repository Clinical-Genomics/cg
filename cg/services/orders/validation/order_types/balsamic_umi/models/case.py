from pydantic import Discriminator, Tag
from typing_extensions import Annotated

from cg.services.orders.validation.models.discriminators import has_internal_id
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic_umi.models.sample import BalsamicUmiSample

NewSample = Annotated[BalsamicUmiSample, Tag("new")]
OldSample = Annotated[ExistingSample, Tag("existing")]


class BalsamicUmiCase(BalsamicCase):
    samples: list[Annotated[NewSample | OldSample, Discriminator(has_internal_id)]]
