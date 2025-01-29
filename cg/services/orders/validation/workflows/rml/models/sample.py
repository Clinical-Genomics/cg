import logging

from pydantic import BeforeValidator, Field, model_validator
from typing_extensions import Annotated

from cg.models.orders.sample_base import ContainerEnum, ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import IndexEnum
from cg.services.orders.validation.index_sequences import INDEX_SEQUENCES
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.utils import parse_control

LOG = logging.getLogger(__name__)


class RmlSample(Sample):
    concentration: float
    concentration_sample: float | None = None
    container: ContainerEnum | None = Field(default=None, exclude=True)
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    index: IndexEnum
    index_number: int | None = None
    index_sequence: str | None = None
    pool: str
    priority: PriorityEnum
    rml_plate_name: str | None = None
    volume: int
    well_position_rml: str | None = None

    @model_validator(mode="after")
    def set_default_index_sequence(self) -> "RmlSample":
        """Set a default index_sequence from the index and index_number."""
        if not self.index_sequence and (self.index and self.index_number):
            try:
                self.index_sequence = INDEX_SEQUENCES[self.index][self.index_number - 1]
            except Exception:
                LOG.warning(
                    f"No index sequence set and no suitable sequence found for index {self.index}, number {self.index_number}"
                )
        return self
