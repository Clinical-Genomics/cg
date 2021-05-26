from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class UpploadFiles(BaseModel):
    result_file: Path
    multiqc_report: Optional[Path]
    segmental_calls: Optional[Path]
