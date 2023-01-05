"""Module for modeling flow cells."""
import datetime
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError
from typing_extensions import Literal

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError
from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import SampleSheet, get_sample_sheet_from_file
from cgmodels.exceptions import SampleSheetError

LOG = logging.getLogger(__name__)


class FlowCell:
    """Class to collect information about flow cell directories and there particular files."""

    def __init__(self, flow_cell_path: Path, bcl_converter: Optional[str] = "bcl2fastq"):
        LOG.debug(f"Instantiating FlowCell with path {flow_cell_path}")
        self.path: Path = flow_cell_path
        self.bcl_converter: Optional[str] = bcl_converter
        self._run_parameters: Optional[RunParameters] = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_name: str = ""
        self.machine_number: int = 0
        self.base_name: str = ""  # Base name is flow cell-id + flow cell position
        self.id: str = ""
        self.position: Literal["A", "B"] = "A"
        self.parse_flow_cell_name()

    def parse_flow_cell_name(self):
        """Parse relevant information from flow cell name.

        This will assume that the flow cell naming convention is used. If not we skip the flow cell.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '201203_A00689_0200_AHVKJCDRXX'.
        """

        self.validate_flow_cell_name()
        self.run_date = datetime.datetime.strptime(self.split_flow_cell_name[0], "%y%m%d")
        self.machine_name = self.split_flow_cell_name[1]
        self.machine_number = int(self.split_flow_cell_name[2])
        base_name: str = self.split_flow_cell_name[-1]
        self.base_name = base_name
        LOG.debug(f"Set flow cell id to {base_name}")
        self.id = base_name[1:]
        self.position = base_name[0]

    @property
    def split_flow_cell_name(self) -> List[str]:
        """Return split flow cell name."""
        return self.path.name.split("_")

    @property
    def full_name(self) -> str:
        """Return flow cell full name."""
        return self.path.name

    @property
    def sample_sheet_path(self) -> Path:
        """Return sample sheet path."""
        return Path(self.path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)

    @property
    def run_parameters_path(self) -> Path:
        """Return path to run parameters file."""
        return Path(self.path, DemultiplexingDirsAndFiles.RUN_PARAMETERS)

    @property
    def run_parameters_object(self) -> RunParameters:
        """Return run parameters object."""
        if not self.run_parameters_path.exists():
            message = f"Could not find run parameters file {self.run_parameters_path}"
            LOG.warning(message)
            raise FileNotFoundError(message)
        if not self._run_parameters:
            self._run_parameters = RunParameters(run_parameters_path=self.run_parameters_path)
        return self._run_parameters

    @property
    def rta_complete_path(self) -> Path:
        """Return RTAComplete path."""
        return Path(self.path, DemultiplexingDirsAndFiles.RTACOMPLETE)

    @property
    def copy_complete_path(self) -> Path:
        """Return copy complete path."""
        return Path(self.path, DemultiplexingDirsAndFiles.COPY_COMPLETE)

    @property
    def hiseq_x_copy_complete_path(self) -> Path:
        """Return copy complete path for Hiseq X."""
        return Path(self.path, DemultiplexingDirsAndFiles.Hiseq_X_COPY_COMPLETE)

    @property
    def hiseq_x_delivery_started_path(self) -> Path:
        """Return delivery started path for Hiseq X."""
        return Path(self.path, DemultiplexingDirsAndFiles.DELIVERY)

    @property
    def demultiplexing_started_path(self) -> Path:
        """Return demux started path."""
        return Path(self.path, DemultiplexingDirsAndFiles.DEMUX_STARTED)

    @property
    def trailblazer_config_path(self) -> Path:
        """Return file to SLURM job ids path."""
        return Path(self.path, "slurm_job_ids.yaml")

    @property
    def hiseq_x_flow_cell(self) -> Path:
        """Return path to Hiseq X flow cell directory."""
        return Path(self.path, DemultiplexingDirsAndFiles.HiseqX_TILE_DIR)

    def validate_flow_cell_name(self) -> None:
        """
        Validate on the following criteria:
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '201203_A00689_0200_AHVKJCDRXX'.
        """
        if len(self.split_flow_cell_name) != 4:
            message = f"Flowcell {self.path.name} does not follow the flow cell naming convention"
            LOG.warning(message)
            raise FlowCellError(message)

    def is_demultiplexing_started(self) -> bool:
        """Check if demultiplexing started path exists."""
        return self.demultiplexing_started_path.exists()

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists."""
        LOG.info("Check if sample sheet exists")
        return self.sample_sheet_path.exists()

    def validate_sample_sheet(self) -> bool:
        """Validate if sample sheet is on correct format."""
        try:
            get_sample_sheet_from_file(
                infile=self.sample_sheet_path, sheet_type="S4", bcl_converter=self.bcl_converter
            )
        except (SampleSheetError, ValidationError) as error:
            LOG.warning("Invalid sample sheet")
            LOG.warning(error)
            return False
        return True

    def get_sample_sheet(self) -> SampleSheet:
        """Return sample sheet object."""
        return get_sample_sheet_from_file(
            infile=self.sample_sheet_path, sheet_type="S4", bcl_converter=self.bcl_converter
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

    def is_hiseq_x_copy_completed(self) -> bool:
        """Check if copy of Hiiseq X flow cell is done."""
        LOG.info("Check if copy of data from Hiseq X sequence instrument is ready")
        return self.hiseq_x_copy_complete_path.exists()

    def is_hiseq_x_delivery_started(self) -> bool:
        """Check if delivery of Hiseq X flow cell is started."""
        LOG.info("Check if delivery of data from Hiseq X sequence instrument is ready")
        return self.hiseq_x_delivery_started_path.exists()

    def is_hiseq_x(self) -> bool:
        """Check if flow cell is Hiseq X."""
        LOG.debug("Check if flow cell is Hiseq X")
        return self.hiseq_x_flow_cell.exists()

    def is_flow_cell_ready(self) -> bool:
        """Check if a flow cell is ready for demultiplexing.

        A flow cell is ready if the two files RTAComplete.txt and CopyComplete.txt exists in the
        flow cell directory.
        """
        LOG.info("Check if flow cell is ready for demultiplexing")
        if not self.is_sequencing_done():
            LOG.info(f"Sequencing is not completed for flow cell {self.id}")
            return False
        LOG.debug(f"Sequence is done for flow cell {self.id}")
        if not self.is_copy_completed():
            LOG.info(f"Copy of sequence data is not ready for flow cell {self.id}")
            return False
        LOG.debug(f"All data has been transferred for flow cell {self.id}")
        LOG.info(f"Flow cell {self.id} is ready for demultiplexing")
        return True

    def __str__(self):
        return f"FlowCell(path={self.path},run_parameters_path={self.run_parameters_path})"
