from typing import Optional
from pydantic import BaseModel


class UploadFiles(BaseModel):
    result_file: str
    multiqc_report: Optional[str]
    segmental_calls: Optional[str]
