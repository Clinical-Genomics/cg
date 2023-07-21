from typing import Optional
from pydantic.v1 import BaseModel


class StatinaUploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str]
    segmental_calls: Optional[str]
