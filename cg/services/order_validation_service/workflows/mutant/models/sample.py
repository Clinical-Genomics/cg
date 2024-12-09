from datetime import date

from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.order_validation_service.constants import (
    ElutionBuffer,
    ExtractionMethod,
)
from cg.services.order_validation_service.models.sample import Sample
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
    control: ControlEnum
    elution_buffer: ElutionBuffer
    extraction_method: ExtractionMethod
    organism: str
    original_lab: OriginalLab
    pre_processing_method: PreProcessingMethod
    primer: Primer
    priority: PriorityEnum
    quantity: int | None = None
    reference_genome: str
    region: Region
    selection_criteria: SelectionCriteria
