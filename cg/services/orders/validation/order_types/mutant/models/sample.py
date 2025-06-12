from datetime import date

from pydantic import BeforeValidator, PrivateAttr, field_serializer, model_validator
from typing_extensions import Annotated

from cg.constants.orderforms import ORIGINAL_LAB_ADDRESSES, REGION_CODES
from cg.models.orders.sample_base import ControlEnum, PriorityEnum
from cg.services.orders.validation.constants import ElutionBuffer, ExtractionMethod
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.order_types.mutant.constants import (
    OriginalLab,
    PreProcessingMethod,
    Primer,
    Region,
    SelectionCriteria,
)
from cg.services.orders.validation.utils import parse_buffer, parse_control, parse_extraction_method


class MutantSample(Sample):
    collection_date: date
    concentration_sample: float | None = None
    control: Annotated[ControlEnum, BeforeValidator(parse_control)] = ControlEnum.not_control
    elution_buffer: Annotated[ElutionBuffer, BeforeValidator(parse_buffer)]
    extraction_method: Annotated[ExtractionMethod, BeforeValidator(parse_extraction_method)]
    _lab_code: str = PrivateAttr(default="SE100 Karolinska")
    organism: str
    organism_other: str | None = None
    original_lab: OriginalLab
    original_lab_address: str
    pre_processing_method: PreProcessingMethod
    primer: Primer
    priority: PriorityEnum
    quantity: int | None = None
    reference_genome: str
    region: Region
    region_code: str
    selection_criteria: SelectionCriteria
    _verified_organism: bool | None = PrivateAttr(default=None)

    @model_validator(mode="before")
    @classmethod
    def set_original_lab_address(cls, data: any) -> any:
        if isinstance(data, dict):
            is_set = bool(data.get("original_lab_address"))
            if not is_set and data.get("original_lab"):
                data["original_lab_address"] = ORIGINAL_LAB_ADDRESSES[data["original_lab"]]
        return data

    @model_validator(mode="before")
    @classmethod
    def set_region_code(cls, data: any) -> any:
        if isinstance(data, dict):
            is_set = bool(data.get("region_code"))
            if not is_set and data.get("region"):
                data["region_code"] = REGION_CODES[data["region"]]
        return data

    @field_serializer("collection_date")
    def serialize_collection_date(self, value: date) -> str:
        return value.isoformat()

    def model_dump(self, **kwargs) -> dict:
        data = super().model_dump(**kwargs)
        data["lab_code"] = self._lab_code
        data["verified_organism"] = self._verified_organism
        return data
