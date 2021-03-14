from pydantic import BaseModel


class SbatchError(BaseModel):
    flowcell_name: str
    email: str
    logfile: str


class SbatchCommand(BaseModel):
    run_dir: str  # path/to/a_flowcell/
    out_dir: str  # path/to/output_dir/
    basemask: str  # path/to/basemask.txt
    sample_sheet: str  # path/to/SampleSheet.csv
