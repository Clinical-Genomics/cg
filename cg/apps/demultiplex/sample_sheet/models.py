import logging
from pydantic import BaseModel, Field
from typing import List

from cg.constants.demultiplexing import SampleSheetHeaderColumnNames

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """This model is used when parsing/validating existing sample sheets."""

    lane: int = Field(..., alias=SampleSheetHeaderColumnNames.LANE.value)
    sample_id: str = Field(..., alias="Sample_ID")
    index: str = Field(..., alias="Index")
    index2: str = ""
    override_cycles: str = Field(..., alias="Index")
    adapter_read1: str = Field("", alias="AdapterRead1")
    adapter_read2: str = Field("", alias="AdapterRead2")
    barcode_mismatches_index1: int = Field(0, alias="BarcodeMismatchesIndex1")
    barcode_mismatches_index2: int = Field(0, alias="BarcodeMismatchesIndex2")

    class Config:
        allow_population_by_field_name = True


class SampleSheet(BaseModel):
    samples: List[FlowCellSample]
