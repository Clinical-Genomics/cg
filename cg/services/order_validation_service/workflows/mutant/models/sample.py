from datetime import date

from pydantic import BeforeValidator, PrivateAttr
from typing_extensions import Annotated

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import ElutionBuffer, ExtractionMethod
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.utils import (
    parse_buffer,
    parse_control,
    parse_extraction_method,
)
from cg.services.order_validation_service.workflows.mutant.constants import (
    OriginalLab,
    PreProcessingMethod,
    Primer,
    Region,
    SelectionCriteria,
)


class MutantSample(Sample):
    collection_date: date
    concentration_sample: float | None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    extraction_method: Annotated[ExtractionMethod, BeforeValidator(parse_extraction_method)]
    organism: str
    original_lab: OriginalLab
    pre_processing_method: PreProcessingMethod
    primer: Primer
    priority: PriorityEnum
    quantity: int | None = None
    reference_genome: str
    region: Region
    selection_criteria: SelectionCriteria
    _verified_organism: str | None = PrivateAttr(default=None)
