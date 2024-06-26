"""Module for modeling flow cells."""

import datetime
import logging
import os
from pathlib import Path
from typing import Type

from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_path
from cg.constants.constants import LENGTH_LONG_DATE
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import SEQUENCER_TYPES, Sequencers
from cg.constants.symbols import EMPTY_STRING
from cg.exc import FlowCellError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersHiSeq,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)
from cg.models.run_devices.utils import parse_date
from cg.services.parse_run_completion_status_service.parse_run_completion_status_service import (
    ParseRunCompletionStatusService,
)
from cg.utils.files import get_source_creation_time_stamp
from cg.utils.time import format_time_from_ctime

LOG = logging.getLogger(__name__)
RUN_PARAMETERS_CONSTRUCTOR: dict[str, Type] = {
    Sequencers.HISEQGA: RunParametersHiSeq,
    Sequencers.HISEQX: RunParametersHiSeq,
    Sequencers.NOVASEQ: RunParametersNovaSeq6000,
    Sequencers.NOVASEQX: RunParametersNovaSeqX,
}


class IlluminaRunDirectoryData:
    """Class to collect information about sequencing run directories and their particular files."""

    def __init__(self, sequencing_run_path: Path):
        LOG.debug(f"Instantiating IlluminaRunDirectoryData with path {sequencing_run_path}")
        self.path: Path = sequencing_run_path
        self.machine_name: str = EMPTY_STRING
        self._run_parameters: RunParameters | None = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_number: int = 0
        self.base_name: str = EMPTY_STRING  # Base name is flow cell-id + flow cell position
        self.id: str = EMPTY_STRING
        self.position: Literal["A", "B"] = "A"
        self.parse_sequencing_run_dir_name()
        self._sample_sheet_path_hk: Path | None = None
        self.sample_sheet_validator = SampleSheetValidator()

    def parse_sequencing_run_dir_name(self):
        """Parse relevant information from sequencing run name.
        This will assume that the sequencing run naming convention is used. If not we skip the sequencing run.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '230912_A00187_1009_AHK33MDRX3'.
        """

        self.validate_sequencing_run_dir_name()
        self.run_date = self._parse_date()
        self.machine_name = self.split_sequencing_run_name[1]
        self.machine_number = int(self.split_sequencing_run_name[2])
        base_name: str = self.split_sequencing_run_name[-1]
        self.base_name = base_name
        LOG.debug(f"Set sequencing run id to {base_name}")
        self.id = base_name[1:]
        self.position = base_name[0]

    @property
    def split_sequencing_run_name(self) -> list[str]:
        """Return split sequencing run name."""
        return self.path.name.split("_")

    @property
    def full_name(self) -> str:
        """Return sequencing run full name."""
        return self.path.name

    @property
    def sequenced_at(self) -> list[str]:
        """Return the sequencing date for the sequencing run."""
        date_part: str = self.full_name.split("_")[0]
        return parse_date(date_part)

    @property
    def sample_sheet_path(self) -> Path:
        """
        Return sample sheet path.
        """
        return Path(
            self.get_sequencing_runs_dir(), DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
        )

    def set_sample_sheet_path_hk(self, hk_path: Path):
        self._sample_sheet_path_hk = hk_path

    def get_sample_sheet_path_hk(self) -> Path:
        if not self._sample_sheet_path_hk:
            raise FlowCellError("Attribute _sample_sheet_path_hk has not been assigned yet")
        return self._sample_sheet_path_hk

    def get_sequencing_runs_dir(self) -> Path:
        """
        Return the flow cells run directory regardless of the path used to initialise the IlluminaRunDirectoryData.
        """
        current_path: str = self.path.as_posix()
        if DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME in current_path:
            return Path(
                str.replace(
                    current_path,
                    DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME,
                    DemultiplexingDirsAndFiles.SEQUENCING_RUNS_DIRECTORY_NAME,
                )
            )
        return self.path

    def get_demultiplexed_runs_dir(self) -> Path:
        """
        Return the demultiplexed run directory regardless of the path used to initialise the IlluminaRunDirectoryData.
        """
        current_path: str = self.path.as_posix()
        if DemultiplexingDirsAndFiles.SEQUENCING_RUNS_DIRECTORY_NAME in current_path:
            return Path(
                str.replace(
                    current_path,
                    DemultiplexingDirsAndFiles.SEQUENCING_RUNS_DIRECTORY_NAME,
                    DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME,
                )
            )
        return self.path

    @property
    def run_parameters_path(self) -> Path:
        """Return path to run parameters file if it exists.
        Raises:
            FlowCellError if the sequencing run has no run parameters file."""
        flow_cell_run_dir: Path = self.get_sequencing_runs_dir()
        if DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE in os.listdir(flow_cell_run_dir):
            return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)
        elif DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE in os.listdir(flow_cell_run_dir):
            return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE)
        else:
            message: str = f"No run parameters file found in sequencing run {flow_cell_run_dir}"
            LOG.error(message)
            raise FlowCellError(message)

    @property
    def run_parameters(self) -> RunParameters:
        """Return run parameters object."""
        if not self._run_parameters:
            self._run_parameters = RUN_PARAMETERS_CONSTRUCTOR[self.sequencer_type](
                run_parameters_path=self.run_parameters_path
            )
        return self._run_parameters

    @property
    def sequencer_type(
        self,
    ) -> Literal[Sequencers.HISEQX, Sequencers.HISEQGA, Sequencers.NOVASEQ, Sequencers.NOVASEQX]:
        """Return the sequencer type."""
        return SEQUENCER_TYPES[self.machine_name]

    @property
    def rta_complete_path(self) -> Path:
        """Return RTAComplete path."""
        return Path(self.get_sequencing_runs_dir(), DemultiplexingDirsAndFiles.RTACOMPLETE)

    @property
    def copy_complete_path(self) -> Path:
        """Return copy complete path."""
        return Path(self.get_sequencing_runs_dir(), DemultiplexingDirsAndFiles.COPY_COMPLETE)

    @property
    def demultiplexing_started_path(self) -> Path:
        """Return demux started path."""
        flow_cell_run_dir: Path = self.get_sequencing_runs_dir()
        return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.DEMUX_STARTED)

    @property
    def demultiplex_software_info_path(self) -> Path:
        """Return demultiplex software info path."""
        demux_run_dir = self.get_demultiplexed_runs_dir()
        return Path(demux_run_dir, DemultiplexingDirsAndFiles.DEMUX_VERSION_FILE)

    @property
    def demux_complete_path(self) -> Path:
        """Return demux complete path."""
        demux_run_dir = self.get_demultiplexed_runs_dir()
        return Path(demux_run_dir, DemultiplexingDirsAndFiles.DEMUX_COMPLETE)

    @property
    def trailblazer_config_path(self) -> Path:
        """Return file to SLURM job ids path."""
        return Path(self.get_sequencing_runs_dir(), "slurm_job_ids.yaml")

    @property
    def is_demultiplexing_complete(self) -> bool:
        return Path(self.demux_complete_path).exists()

    def _parse_date(self):
        """Return the parsed date in the correct format."""
        if len(self.split_sequencing_run_name[0]) == LENGTH_LONG_DATE:
            return datetime.datetime.strptime(self.split_sequencing_run_name[0], "%Y%m%d")
        return datetime.datetime.strptime(self.split_sequencing_run_name[0], "%y%m%d")

    def validate_sequencing_run_dir_name(self) -> None:
        """
        Validate on the following criteria:
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '230912_A00187_1009_AHK33MDRX3'.
        """
        if len(self.split_sequencing_run_name) != 4:
            message = (
                f"Flowcell {self.full_name} does not follow the sequencing run naming convention"
            )
            LOG.warning(message)
            raise FlowCellError(message)

    def has_demultiplexing_started_locally(self) -> bool:
        """Check if demultiplexing has started path exists on the cluster."""
        return self.demultiplexing_started_path.exists()

    def has_demultiplexing_started_on_sequencer(self) -> bool:
        """Check if demultiplexing has started on the NovaSeqX machine."""
        latest_analysis: Path = get_latest_analysis_path(self.get_demultiplexed_runs_dir())
        if not latest_analysis:
            return False
        return Path(
            latest_analysis, DemultiplexingDirsAndFiles.DATA, DemultiplexingDirsAndFiles.BCL_CONVERT
        ).exists()

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists."""
        LOG.info("Check if sample sheet exists")
        return self.sample_sheet_path.exists()

    @property
    def sample_sheet(self) -> SampleSheet:
        """Return sample sheet object."""
        if not self._sample_sheet_path_hk:
            raise FlowCellError("Sample sheet path has not been assigned yet")
        return self.sample_sheet_validator.get_sample_sheet_object_from_file(
            file_path=self._sample_sheet_path_hk
        )

    def is_sequencing_done(self) -> bool:
        """Check if sequencing is done.
        This is indicated by that the file RTAComplete.txt exists.
        """
        LOG.info("Check if sequencing is done")
        return self.rta_complete_path.exists()

    def is_copy_completed(self) -> bool:
        """Check if copy of sequencing run is done.
        This is indicated by that the file CopyComplete.txt exists.
        """
        LOG.info("Check if copy of data from sequence instrument is ready")
        return self.copy_complete_path.exists()

    def is_sequencing_run_ready(self) -> bool:
        """Check if a sequencing run is ready for downstream processing.

        A sequencing run is ready if the two files RTAComplete.txt and CopyComplete.txt exist in the
        sequencing run directory.
        """
        LOG.info("Check if sequencing run is ready for downstream processing")
        if not self.is_sequencing_done():
            LOG.warning(f"Sequencing is not completed for sequencing run {self.id}")
            return False
        LOG.debug(f"Sequence is done for sequencing run {self.id}")
        if not self.is_copy_completed():
            LOG.warning(f"Copy of sequence data is not ready for sequencing run {self.id}")
            return False
        LOG.debug(f"All data has been transferred for sequencing run {self.id}")
        LOG.info(f"Sequencing run {self.id} is ready for downstream processing")
        return True

    def get_run_completion_status(self) -> Path | None:
        """Return the run completion status path."""
        flow_cells_dir: Path = self.get_sequencing_runs_dir()
        file_path = Path(flow_cells_dir, DemultiplexingDirsAndFiles.RUN_COMPLETION_STATUS)
        if file_path.exists():
            return file_path
        return None

    @property
    def sequencing_started_at(self) -> datetime.datetime | None:
        parser = ParseRunCompletionStatusService()
        file_path: Path = self.get_run_completion_status()
        return parser.get_start_time(file_path) if file_path else None

    @property
    def sequencing_completed_at(self) -> datetime.datetime | None:
        parser = ParseRunCompletionStatusService()
        file_path: Path = self.get_run_completion_status()
        return parser.get_end_time(file_path) if file_path else None

    @property
    def demultiplexing_started_at(self) -> datetime.datetime | None:
        """Get the demultiplexing started time stamp from the sequencing run dir."""
        try:
            time: float = get_source_creation_time_stamp(self.demultiplexing_started_path)
            return format_time_from_ctime(time)
        except FileNotFoundError:
            return None

    @property
    def demultiplexing_completed_at(self) -> datetime.datetime | None:
        """Get the demultiplexing completed time stamp from the demultiplexed runs dir."""
        try:
            time: float = get_source_creation_time_stamp(self.demux_complete_path)
            return format_time_from_ctime(time)
        except FileNotFoundError:
            return None

    def __str__(self):
        return f"FlowCell(path={self.path},run_parameters_path={self.run_parameters_path})"


def get_sequencing_runs_from_path(sequencing_run_dir: Path) -> list[IlluminaRunDirectoryData]:
    """Return sequencing run objects from sequencing run dir."""
    sequencing_runs: list[IlluminaRunDirectoryData] = []
    LOG.debug(f"Search for flow cells ready to encrypt in {sequencing_run_dir}")
    for run_dir in sequencing_run_dir.iterdir():
        if not run_dir.is_dir():
            continue
        LOG.debug(f"Found directory: {run_dir}")
        try:
            sequencing_run = IlluminaRunDirectoryData(sequencing_run_path=run_dir)
        except FlowCellError:
            continue
        sequencing_runs.append(sequencing_run)
    return sequencing_runs
