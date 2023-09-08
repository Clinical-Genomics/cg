"""Models for Fluffy sample sheets."""
import datetime as dt

from pathlib import Path
from pydantic import BaseModel
from typing import List

from cg.utils.enums import StrEnum


class FluffySampleSheetHeader(StrEnum):
    """Class that represents the headers in a Fluffy sample sheet."""

    flow_cell_id: str = "FCID"
    lane: str = "Lane"
    sample_internal_id: str = "Sample_ID"
    sample_reference: str = "SampleRef"
    index: str = "index"
    index2: str = "index2"
    sample_name: str = "SampleName"
    control: str = "Control"
    recipe: str = "Recipe"
    operator: str = "Operator"
    sample_project: str = "SampleProject"
    exclude: str = "Exclude"
    library_nM: str = "Library_nM"
    sequencing_date: str = "SequencingDate"


class FluffySampleSheetEntry(BaseModel):
    """Class that represents a sample entry in a Fluffy sample sheet."""

    flow_cell_id: str
    lane: int
    sample_internal_id: str
    sample_reference: str = "hg19"
    index: str
    index2: str
    sample_name: str
    control: str = "N"
    recipe: str = "R1"
    operator: str = "script"
    sample_project: str
    exclude: bool
    library_nM: float
    sequencing_date: dt.date


class FluffySampleSheet(BaseModel):
    """Class that represents a Fluffy sample sheet."""

    header: FluffySampleSheetHeader
    entries: List[FluffySampleSheetEntry]

    def write_sample_sheet(self, out_path: Path) -> None:
        """Write the sample sheet to a file."""
        with out_path.open("w") as outfile:
            outfile.write(",".join([column.value for column in self.header]) + "\n")
            for entry in self.entries:
                outfile.write(",".join([entry.model_dump()[column.value] for column in self.header]) + "\n")
