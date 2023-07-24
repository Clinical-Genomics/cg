from pydantic.v1 import BaseModel
from typing_extensions import Literal


class SbatchError(BaseModel):
    flow_cell_id: str
    email: str
    logfile: str
    demux_dir: str
    demux_started: str


class SbatchCommand(BaseModel):
    run_dir: str  # path/to/a_flowcell/
    demux_dir: str  # path/to/output_dir/
    unaligned_dir: str  # path/to/output_dir/Unaligned/
    sample_sheet: str  # path/to/SampleSheet.csv
    demux_completed_file: str  # path/to/demuxcomplete.txt
    environment: Literal["stage", "production"]
