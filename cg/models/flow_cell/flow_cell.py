"""Module for modeling flow cells."""
import datetime
import logging
import os
from pathlib import Path
from typing import Type

from pydantic import ValidationError
from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
    SampleSheet,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_sheet_from_file,
)
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import get_latest_analysis_path
from cg.constants.bcl_convert_metrics import SAMPLE_SHEET_HEADER
from cg.constants.constants import LENGTH_LONG_DATE
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import SEQUENCER_TYPES, Sequencers
from cg.exc import FlowCellError, SampleSheetError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersHiSeq,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)
from cg.models.flow_cell.utils import parse_date

LOG = logging.getLogger(__name__)
RUN_PARAMETERS_CONSTRUCTOR: dict[str, Type] = {
    Sequencers.HISEQGA: RunParametersHiSeq,
    Sequencers.HISEQX: RunParametersHiSeq,
    Sequencers.NOVASEQ: RunParametersNovaSeq6000,
    Sequencers.NOVASEQX: RunParametersNovaSeqX,
}


class FlowCellDirectoryData:
    """Class to collect information about flow cell directories and their particular files."""

    def __init__(self, flow_cell_path: Path, bcl_converter: str | None = None):
        LOG.debug(f"Instantiating FlowCellDirectoryData with path {flow_cell_path}")
        self.path: Path = flow_cell_path
        self.machine_name: str = ""
        self._run_parameters: RunParameters | None = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_number: int = 0
        self.base_name: str = ""  # Base name is flow cell-id + flow cell position
        self.id: str = ""
        self.position: Literal["A", "B"] = "A"
        self.parse_flow_cell_dir_name()
        self.bcl_converter: str = self.get_bcl_converter(bcl_converter)
        self._sample_sheet_path_hk: Path | None = None

    def parse_flow_cell_dir_name(self):
        """Parse relevant information from flow cell name.
        This will assume that the flow cell naming convention is used. If not we skip the flow cell.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '201203_D00483_0200_AHVKJCDRXX'.
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

    @property
    def run_parameters_path(self) -> Path:
        """Return path to run parameters file if it exists.
        Raises:
            FlowCellError if the flow cell has no run parameters file."""
        if DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE in os.listdir(self.path):
            return Path(self.path, DemultiplexingDirsAndFiles.RUN_PARAMETERS_PASCAL_CASE)
        elif DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE in os.listdir(self.path):
            return Path(self.path, DemultiplexingDirsAndFiles.RUN_PARAMETERS_CAMEL_CASE)
        else:
            message: str = f"No run parameters file found in flow cell {self.path}"
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
    def sample_type(
        self,
    ) -> Type[FlowCellSampleBcl2Fastq] | Type[FlowCellSampleBCLConvert]:
        """Return the sample class used in the flow cell."""
        if self.bcl_converter == BclConverter.BCL2FASTQ:
            return FlowCellSampleBcl2Fastq
        return FlowCellSampleBCLConvert

    @property
    def sequencer_type(
        self,
    ) -> Literal[Sequencers.HISEQX, Sequencers.HISEQGA, Sequencers.NOVASEQ, Sequencers.NOVASEQX]:
        """Return the sequencer type."""
        return SEQUENCER_TYPES[self.machine_name]

    def get_bcl_converter(self, bcl_converter: str) -> str:
        """
        Return the BCL converter to use.
        Tries to get the BCL converter from the sequencer type if not provided.
        Note: bcl_converter can be used to override automatic selection.
        Reason: Data reproducibility.
        """
        return bcl_converter or self.get_bcl_converter_by_sequencer()

    def get_bcl_converter_by_sequencer(
        self,
    ) -> str:
        """Return the BCL converter based on the sequencer."""
        if self.sequencer_type in [Sequencers.NOVASEQ, Sequencers.NOVASEQX]:
            LOG.debug(f"Using BCL converter: {BclConverter.DRAGEN}")
            return BclConverter.DRAGEN
        LOG.debug(f"Using BCL converter: {BclConverter.BCL2FASTQ}")
        return BclConverter.BCL2FASTQ

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
        """Return copy complete path for HiSeqX."""
        return Path(self.path, DemultiplexingDirsAndFiles.HISEQ_X_COPY_COMPLETE)

    @property
    def hiseq_x_delivery_started_path(self) -> Path:
        """Return delivery started path for HiSeqX."""
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
    def is_demultiplexing_complete(self) -> bool:
        return Path(self.path, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()

    def _parse_date(self):
        """Return the parsed date in the correct format."""
        if len(self.split_flow_cell_name[0]) == LENGTH_LONG_DATE:
            return datetime.datetime.strptime(self.split_flow_cell_name[0], "%Y%m%d")
        return datetime.datetime.strptime(self.split_flow_cell_name[0], "%y%m%d")

    def validate_flow_cell_dir_name(self) -> None:
        """
        Validate on the following criteria:
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flow_cell_id>
        Example: '201203_D00483_0200_AHVKJCDRXX'.
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

    def validate_sample_sheet(self) -> bool:
        """Validate if sample sheet is on correct format."""
        try:
            get_sample_sheet_from_file(self.sample_sheet_path)
        except (SampleSheetError, ValidationError) as error:
            LOG.warning("Invalid sample sheet")
            LOG.warning(error)
            LOG.warning(
                f"Ensure that the headers in the sample sheet follows the allowed structure for {self.bcl_converter} i.e. \n"
                + SAMPLE_SHEET_HEADER[self.bcl_converter]
            )
            return False
        return True

    @property
    def sample_sheet(self) -> SampleSheet:
        """Return sample sheet object."""
        if not self._sample_sheet_path_hk:
            raise FlowCellError("Sample sheet path has not been assigned yet")
        return get_sample_sheet_from_file(self._sample_sheet_path_hk)

    def get_sample_sheet(self) -> SampleSheet:
        """Return sample sheet object."""
        return get_sample_sheet_from_file(self.sample_sheet_path)

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
