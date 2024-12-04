from pathlib import Path
from pydantic import BaseModel


class FastqFile(BaseModel):
    sample_name: str
    fastq_file_path: Path
