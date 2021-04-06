from pydantic import BaseModel
from typing_extensions import Literal


class SbatchError(BaseModel):
    flowcell_name: str
    email: str
    logfile: str
    out_dir: str
    demux_started: str


class SbatchCommand(BaseModel):
    run_dir: str  # path/to/a_flowcell/
    out_dir: str  # path/to/output_dir/
    sample_sheet: str  # path/to/SampleSheet.csv
    demux_completed_file: str  # path/to/demuxcomplete.txt
    environment: Literal["stage", "production"]
