import datetime
import logging
import socket
from pathlib import Path
from typing import Iterable

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.demultiplex.flowcell import Flowcell
from pydantic import BaseModel
from typing_extensions import Literal

LOG = logging.getLogger(__name__)


class LogfileParameters(BaseModel):
    id_string: str  # This indicate software and version
    # This is the binary that was executed (atm only bcl2fastq)
    program: Literal["bcl2fastq"] = "bcl2fastq"
    command_line: str
    time: datetime.datetime


class DemuxResults:
    """Class to gather information from a demultiplex result"""

    def __init__(self, demux_dir: Path, flowcell: Flowcell):
        self.demux_dir: Path = demux_dir
        self.flowcell: Flowcell = flowcell

    @property
    def run_name(self) -> str:
        return self.demux_dir.name

    @property
    def run_date(self) -> datetime.date:
        raw_time: str = self.run_name.split("_")[0]
        time_object: datetime.datetime = datetime.datetime.strptime(raw_time, "%y%m%d")
        return time_object.date()

    @property
    def machine_name(self) -> str:
        return self.run_name.split("_")[1]

    @property
    def demux_host(self) -> str:
        return socket.gethostname()

    @property
    def conversion_stats_path(self) -> Path:
        return self.results_dir / "Stats" / "ConversionStats.xml"

    @property
    def demux_stats_path(self) -> Path:
        return self.results_dir / "Stats" / "DemultiplexingStats.xml"

    @property
    def log_path(self) -> Path:
        return DemultiplexingAPI.get_logfile(flowcell=self.flowcell)

    @property
    def results_dir(self) -> Path:
        return self.demux_dir / "Unaligned"

    @property
    def sample_sheet_path(self) -> Path:
        return self.flowcell.sample_sheet_path

    @property
    def projects(self) -> Iterable[str]:
        """Return the project names created after demultiplexing

        How do we handle the Project_indexcheck directory?
        """
        for sub_dir in self.results_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            if sub_dir.name.startswith("Project_"):
                project_name: str = sub_dir.name.split("_")[1]
                LOG.debug("Found project %s", project_name)
                yield project_name

    def get_logfile_parameters(self) -> LogfileParameters:
        with open(self.log_path, "r") as logfile:
            for line in logfile.readlines():
                # Fetch the line where the call that was made is
                if "bcl2fastq" in line and "singularity" in line:
                    line = line.strip()
                    split_line = line.split(" ")
                    command_line: str = " ".join(split_line[1:])
                    # Time is in format 20210403115107, YYYYMMDDHHMMSS
                    raw_time: str = split_line[0].strip("[]")  # remove the brackets around the date
                    time: datetime.datetime = datetime.datetime.strptime(raw_time, "%Y%m%d%H%M%S")
                    program = split_line[6]  # get the executed program

                if "bcl2fastq v" in line:
                    id_string = line.strip()
                    break

        return LogfileParameters(
            id_string=id_string, program=program, command_line=command_line, time=time
        )
