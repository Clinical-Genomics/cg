import datetime
import logging
import socket
from pathlib import Path
from typing import Iterable, Optional, Union

from pydantic import BaseModel
from typing_extensions import Literal

from cg.apps.cgstats.parsers.adapter_metrics import AdapterMetrics
from cg.apps.cgstats.parsers.conversion_stats import ConversionStats
from cg.apps.cgstats.parsers.quality_metrics import QualityMetrics
from cg.apps.cgstats.parsers.dragen_demultiplexing_stats import DragenDemultiplexingStats
from cg.apps.cgstats.parsers.run_info import RunInfo
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.constants.demultiplexing import DEMUX_STATS_PATH
from cg.models.demultiplex.flow_cell import FlowCell

LOG = logging.getLogger(__name__)


class LogfileParameters(BaseModel):
    id_string: str  # This indicates software and version
    # This is the binary that was executed (atm only bcl2fastq)
    program: Literal["bcl2fastq", "dragen"] = "bcl2fastq"
    command_line: str
    time: datetime.datetime


class DemuxResults:
    """Class to gather information from a demultiplex result."""

    def __init__(self, demux_dir: Path, flow_cell: FlowCell, bcl_converter: str):
        LOG.info(f"Instantiating DemuxResults with path {demux_dir}")
        self.demux_dir: Path = demux_dir
        self.flow_cell: FlowCell = flow_cell
        self.bcl_converter = bcl_converter
        self._conversion_stats: Optional[ConversionStats] = None
        self._demultiplexing_stats: Optional[DragenDemultiplexingStats] = None
        self._adapter_metrics: Optional[AdapterMetrics] = None
        self._quality_metrics: Optional[QualityMetrics] = None
        self._runinfo: Optional[RunInfo] = None

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
    def conversion_stats(self) -> ConversionStats:
        if self._conversion_stats:
            return self._conversion_stats
        self._conversion_stats = ConversionStats(self.conversion_stats_path)
        return self._conversion_stats

    @property
    def demultiplexing_stats(self) -> DragenDemultiplexingStats:
        if self._demultiplexing_stats:
            return self._demultiplexing_stats
        self._demultiplexing_stats = DragenDemultiplexingStats(self.demux_stats_path)
        return self._demultiplexing_stats

    @property
    def adapter_metrics(self) -> AdapterMetrics:
        if self._adapter_metrics:
            return self._adapter_metrics
        self._adapter_metrics = AdapterMetrics(self.adapter_metrics_path)
        return self._adapter_metrics

    @property
    def quality_metrics(self) -> QualityMetrics:
        if self._quality_metrics:
            return self._quality_metrics
        self._quality_metrics = QualityMetrics(self.quality_metrics_path)
        return self._quality_metrics

    @property
    def run_info(self) -> RunInfo:
        if self._runinfo:
            return self._runinfo
        self._runinfo = RunInfo(self.runinfo_path)
        return self._runinfo

    @property
    def conversion_stats_path(self) -> Union[Path, None]:
        return Path(self.results_dir / DEMUX_STATS_PATH[self.bcl_converter]["conversion_stats"])

    @property
    def demux_stats_path(self) -> Path:
        return Path(self.results_dir / DEMUX_STATS_PATH[self.bcl_converter]["demultiplexing_stats"])

    @property
    def adapter_metrics_path(self) -> Path:
        return Path(self.results_dir, DEMUX_STATS_PATH[self.bcl_converter]["adapter_metrics_stats"])

    @property
    def quality_metrics_path(self) -> Path:
        return Path(self.results_dir, DEMUX_STATS_PATH[self.bcl_converter]["quality_metrics"])

    @property
    def runinfo_path(self) -> Path:
        return Path(self.results_dir, DEMUX_STATS_PATH[self.bcl_converter]["runinfo"])

    @property
    def stderr_log_path(self) -> Path:
        return DemultiplexingAPI.get_stderr_logfile(flow_cell=self.flow_cell)

    @property
    def stdout_log_path(self) -> Path:
        return DemultiplexingAPI.get_stdout_logfile(flow_cell=self.flow_cell)

    @property
    def results_dir(self) -> Path:
        return Path(self.demux_dir, "Unaligned")

    @property
    def sample_sheet_path(self) -> Path:
        """Return the path to where the original sample sheet is"""
        return self.flow_cell.sample_sheet_path

    @property
    def barcode_report(self) -> Path:
        """Return the path to the report with samples with low cluster count"""
        return Path(self.demux_dir, "lane_barcode_summary.csv")

    @property
    def demux_sample_sheet_path(self) -> Path:
        """Return the path to sample sheet in demuxed flowcell dir"""
        return Path(self.results_dir, self.flow_cell.sample_sheet_path.name)

    @property
    def copy_complete_path(self) -> Path:
        """Return the path to a file named copycomplete.txt used as flag that post processing is
        ready."""
        return Path(self.demux_dir, "copycomplete.txt")

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

    @property
    def raw_index_dir(self) -> Path:
        """Return the path to a index dir that is not given the 'Project_'-prefix"""
        return Path(self.results_dir, "indexcheck")

    @property
    def raw_projects(self) -> Iterable[Path]:
        """Return the raw project names created after demultiplexing

        These are either 'indexcheck' or a number
        """
        for sub_dir in self.results_dir.iterdir():
            if not sub_dir.is_dir():
                LOG.debug("Skipping %s since it is not a directory", sub_dir)
                continue
            dir_name: str = sub_dir.name
            if dir_name in {"Stats", "Reports", "Logs"}:
                LOG.debug("Skipping %s dir %s", dir_name, sub_dir)
                continue
            if dir_name.startswith("Project_"):
                LOG.debug("Skipping already renamed project dir %s", sub_dir)
                continue
            if "index" in dir_name:
                LOG.debug("Skipping 'indexcheck' dir %s", sub_dir)
                continue
                # We now know that the rest of the directories are project directories
            yield sub_dir

    def files_renamed(self) -> bool:
        """Assert if the files have been renamed

        Check if the project files have been renamed, in that case it will not need post processing
        """
        return bool(list(self.projects))

    def get_logfile_parameters(self) -> LogfileParameters:
        get_logfile_parameters = {
            "bcl2fastq": self.get_bcl2fastq_logfile_parameters,
            "dragen": self.get_dragen_logfile_parameters,
        }

        return get_logfile_parameters[self.bcl_converter]()

    def get_dragen_logfile_parameters(self) -> LogfileParameters:
        err_log_path: Path = self.stderr_log_path
        out_log_path: Path = self.stdout_log_path

        LOG.info("Parse log file %s", err_log_path)

        if not err_log_path.exists():
            LOG.warning("Could not find log file %s", err_log_path)
            raise FileNotFoundError

        program: str = ""
        time: Optional[datetime.datetime] = None
        command_line: Optional[str] = None
        id_string: Optional[str] = None

        with open(err_log_path, "r") as logfile:
            for line in logfile:
                if "Dragen BCL Convert finished!" in line:
                    time: datetime.datetime = self._parse_time(line)

        LOG.info("Parse log file %s", out_log_path)

        if not out_log_path.exists():
            LOG.warning("Could not find log file %s", out_log_path)
            raise FileNotFoundError

        with open(out_log_path, "r") as logfile:
            for line in logfile:
                if "Command Line" in line:
                    line = line.strip()
                    split_line = line.split(" ")
                    program = split_line[2]
                    command_line = " ".join(split_line[2:])

                if "DRAGEN Host Software Version" in line:
                    line = line.strip()
                    split_line = line.split(" ")
                    id_string = split_line[4]

        return LogfileParameters(
            id_string=id_string, program=program, command_line=command_line, time=time
        )

    def get_bcl2fastq_logfile_parameters(self):
        log_path: Path = self.stderr_log_path

        LOG.info("Parse log file %s", log_path)

        if not log_path.exists():
            LOG.warning("Could not find log file %s", log_path)
            raise FileNotFoundError

        program: str = ""
        time: Optional[datetime.datetime] = None
        command_line: Optional[str] = None
        id_string: Optional[str] = None

        with open(log_path, "r") as logfile:
            for line in logfile:
                # Fetch the line where the call that was made is
                if "bcl2fastq" in line and "singularity" in line:
                    time: datetime.datetime = self._parse_time(line)

                    line = line.strip()
                    split_line = line.split(" ")
                    command_line: str = " ".join(split_line[1:])
                    program = split_line[6]  # get the executed program

                if "bcl2fastq v" in line:
                    id_string = line.strip()
                    break

        return LogfileParameters(
            id_string=id_string, program=program, command_line=command_line, time=time
        )

    @staticmethod
    def _parse_time(line: str) -> datetime.datetime:
        line.strip()
        split_line = line.split(" ")
        raw_time: str = split_line[0].strip("[]")
        try:
            time: datetime.datetime = datetime.datetime.strptime(raw_time, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            time: datetime.datetime = datetime.datetime.strptime(raw_time, "%Y%m%d%H%M%S")

        return time

    def __str__(self):
        return f"DemuxResults(demux_dir={self.demux_dir},flow_cell=FlowCell(flow_cell_path={self.flow_cell.path})"
