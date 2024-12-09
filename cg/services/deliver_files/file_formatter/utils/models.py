from pathlib import Path
from pydantic import BaseModel

from cg.constants.constants import ReadDirection


class FastqFile(BaseModel):
    """A fastq file with a sample name, file path and read direction."""

    sample_name: str
    fastq_file_path: Path
    read_direction: ReadDirection
