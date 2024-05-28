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
from cg.models.flow_cell.utils import parse_date
from cg.services.parse_run_completion_status_service.parse_run_completion_status_service import (
    ParseRunCompletionStatusService,
)
from cg.utils.files import get_source_creation_time_stamp

LOG = logging.getLogger(__name__)
RUN_PARAMETERS_CONSTRUCTOR: dict[str, Type] = {
    Sequencers.HISEQGA: RunParametersHiSeq,
    Sequencers.HISEQX: RunParametersHiSeq,
    Sequencers.NOVASEQ: RunParametersNovaSeq6000,
    Sequencers.NOVASEQX: RunParametersNovaSeqX,
}


class FlowCellDirectoryData:
    """Class to collect information about flow cell directories and their particular files."""

    def __init__(self, flow_cell_path: Path):
        LOG.debug(f"Instantiating FlowCellDirectoryData with path {flow_cell_path}")
        self.path: Path = flow_cell_path
        self.machine_name: str = EMPTY_STRING
        self._run_parameters: RunParameters | None = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_number: int = 0
        self.base_name: str = EMPTY_STRING  # Base name is flow cell-id + flow cell position
        self.id: str = EMPTY_STRING
        self.position: Literal["A", "B"] = "A"
        self.parse_flow_cell_dir_name()
        self._sample_sheet_path_hk: Path | None = None
        self.sample_sheet_validator = SampleSheetValidator()

    def parse_flow_cell_dir_name(self):
        """Parse relevant information from flow cell name.
        This will assume that the flow cell naming convention is used. If not we skip the flow cell.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '230912_A00187_1009_AHK33MDRX3'.
        """

        self.validate_flow_cell_dir_name()
        self.run_date = self._parse_date()
        self.machine_name = self.split_flow_cell_name[1]
        self.machine_number = int(self.split_flow_cell_name[2])
        base_name: str = self.split_flow_cell_name[-1]
        self.base_name = base_name
        LOG.debug(f"Set flow cell id to {base_name}")
        self.id = base_name[1:]
        self.position = base_name[0]

    @property
    def split_flow_cell_name(self) -> list[str]:
        """Return split flow cell name."""
        return self.path.name.split("_")

    @property
    def full_name(self) -> str:
        """Return flow cell full name."""
        return self.path.name

    @property
    def sequenced_at(self) -> list[str]:
        """Return the sequencing date for the flow cell."""
        date_part: str = self.full_name.split("_")[0]
        return parse_date(date_part)

    @property
    def sample_sheet_path(self) -> Path:
        """
        Return sample sheet path.
        """
        return Path(self.path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)

    def set_sample_sheet_path_hk(self, hk_path: Path):
        self._sample_sheet_path_hk = hk_path

    def get_sample_sheet_path_hk(self) -> Path:
        if not self._sample_sheet_path_hk:
            raise FlowCellError("Attribute _sample_sheet_path_hk has not been assigned yet")
        return self._sample_sheet_path_hk

    def get_flow_cell_run_dir(self) -> Path:
        """
        Return the flow cells run directory regardless of the path used to initialise the FlowCellsDirectoryData.
        """
        current_path: str = self.path.as_posix()
        if DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME in current_path:
            return Path(
                str.replace(
                    current_path,
                    DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME,
                    DemultiplexingDirsAndFiles.FLOW_CELLS_DIRECTORY_NAME,
                )
            )
        return self.path

    def get_demultiplexed_runs_dir(self) -> Path:
        """
        Return the flow cells run directory
        if the FlowCellsDirectoryData was initialised with Demultiplexed runs dir.
        """
        current_path: str = self.path.as_posix()
        if DemultiplexingDirsAndFiles.FLOW_CELLS_DIRECTORY_NAME in current_path:
            return Path(
                str.replace(
                    current_path,
                    DemultiplexingDirsAndFiles.FLOW_CELLS_DIRECTORY_NAME,
                    DemultiplexingDirsAndFiles.DEMULTIPLEXED_RUNS_DIRECTORY_NAME,
                )
            )
        return self.path

    @property
    def run_parameters_path(self) -> Path:
        """Return path to run parameters file if it exists.
        Raises:
            FlowCellError if the flow cell has no run parameters file."""
        flow_cell_run_dir: Path = self.get_flow_cell_run_dir()
        if DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE in os.listdir(flow_cell_run_dir):
            return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)
        elif DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE in os.listdir(flow_cell_run_dir):
            return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE)
        else:
            message: str = f"No run parameters file found in flow cell {flow_cell_run_dir}"
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
        return Path(self.path, DemultiplexingDirsAndFiles.RTACOMPLETE)

    @property
    def copy_complete_path(self) -> Path:
        """Return copy complete path."""
        return Path(self.path, DemultiplexingDirsAndFiles.COPY_COMPLETE)

    @property
    def demultiplexing_started_path(self) -> Path:
        """Return demux started path."""
        flow_cell_run_dir: Path = self.get_flow_cell_run_dir()
        return Path(flow_cell_run_dir, DemultiplexingDirsAndFiles.DEMUX_STARTED)

    @property
    def demux_complete_path(self) -> Path:
        """Return demux complete path."""
        demux_run_dir = self.get_demultiplexed_runs_dir()
        return Path(demux_run_dir, DemultiplexingDirsAndFiles.DEMUX_COMPLETE)

    @property
    def trailblazer_config_path(self) -> Path:
        """Return file to SLURM job ids path."""
        return Path(self.path, "slurm_job_ids.yaml")

    @property
    def is_demultiplexing_complete(self) -> bool:
        return Path(self.demux_complete_path).exists()

    def _parse_date(self):
        """Return the parsed date in the correct format."""
        if len(self.split_flow_cell_name[0]) == LENGTH_LONG_DATE:
            return datetime.datetime.strptime(self.split_flow_cell_name[0], "%Y%m%d")
        return datetime.datetime.strptime(self.split_flow_cell_name[0], "%y%m%d")

    def validate_flow_cell_dir_name(self) -> None:
        """
        Validate on the following criteria:
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '230912_A00187_1009_AHK33MDRX3'.
        """
        if len(self.split_flow_cell_name) != 4:
            message = f"Flowcell {self.full_name} does not follow the flow cell naming convention"
            LOG.warning(message)
            raise FlowCellError(message)

    def has_demultiplexing_started_locally(self) -> bool:
        """Check if demultiplexing has started path exists on the cluster."""
        return self.demultiplexing_started_path.exists()

    def has_demultiplexing_started_on_sequencer(self) -> bool:
        """Check if demultiplexing has started on the NovaSeqX machine."""
        latest_analysis: Path = get_latest_analysis_path(self.path)
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
        """Check if copy of flow cell is done.
        This is indicated by that the file CopyComplete.txt exists.
        """
        LOG.info("Check if copy of data from sequence instrument is ready")
        return self.copy_complete_path.exists()

    def is_flow_cell_ready(self) -> bool:
        """Check if a flow cell is ready for downstream processing.

        A flow cell is ready if the two files RTAComplete.txt and CopyComplete.txt exist in the
        flow cell directory.
        """
        LOG.info("Check if flow cell is ready for downstream processing")
        if not self.is_sequencing_done():
            LOG.warning(f"Sequencing is not completed for flow cell {self.id}")
            return False
        LOG.debug(f"Sequence is done for flow cell {self.id}")
        if not self.is_copy_completed():
            LOG.warning(f"Copy of sequence data is not ready for flow cell {self.id}")
            return False
        LOG.debug(f"All data has been transferred for flow cell {self.id}")
        LOG.info(f"Flow cell {self.id} is ready for downstream processing")
        return True

    def get_run_completion_status(self) -> Path | None:
        """Return the run completion status path."""
        flow_cells_dir: Path = self.get_flow_cell_run_dir()
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
    def demultiplexing_started_at(self) -> datetime | None:
        """Get the demultiplexing started time stamp from the flow cell run dir."""
        try:
            return get_source_creation_time_stamp(self.demultiplexing_started_path)
        except FileNotFoundError:
            return None

    @property
    def demultiplexing_completed_at(self) -> datetime:
        """Get the demultiplexing completed time stamp from the demultiplexed runs dir."""
        try:
            return get_source_creation_time_stamp(self.demux_complete_path)
        except FileNotFoundError:
            return None

    def __str__(self):
        return f"FlowCell(path={self.path},run_parameters_path={self.run_parameters_path})"


def get_flow_cells_from_path(flow_cells_dir: Path) -> list[FlowCellDirectoryData]:
    """Return flow cell objects from flow cell dir."""
    flow_cells: list[FlowCellDirectoryData] = []
    LOG.debug(f"Search for flow cells ready to encrypt in {flow_cells_dir}")
    for flow_cell_dir in flow_cells_dir.iterdir():
        if not flow_cell_dir.is_dir():
            continue
        LOG.debug(f"Found directory: {flow_cell_dir}")
        try:
            flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell_dir)
        except FlowCellError:
            continue
        flow_cells.append(flow_cell)
    return flow_cells
