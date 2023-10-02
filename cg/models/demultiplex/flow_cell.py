"""Module for modeling flow cells."""
import datetime
import logging
from pathlib import Path
from typing import List, Optional, Type, Union

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
from cg.constants.sequencing import Sequencers, sequencer_types
from cg.exc import FlowCellError, SampleSheetError
from cg.models.demultiplex.run_parameters import (
    RunParameters,
    RunParametersNovaSeq6000,
    RunParametersNovaSeqX,
)

LOG = logging.getLogger(__name__)


class FlowCellDirectoryData:
    """Class to collect information about flow cell directories and their particular files."""

    def __init__(self, flow_cell_path: Path, bcl_converter: Optional[str] = None):
        LOG.debug(f"Instantiating FlowCellDirectoryData with path {flow_cell_path}")
        self.path: Path = flow_cell_path
        self.machine_name: str = ""
        self._run_parameters: Optional[RunParameters] = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_number: int = 0
        self.base_name: str = ""  # Base name is flow cell-id + flow cell position
        self.id: str = ""
        self.position: Literal["A", "B"] = "A"
        self.parse_flow_cell_dir_name()
        self.bcl_converter: Optional[str] = self.get_bcl_converter(bcl_converter)
        self._sample_sheet_path_hk: Optional[Path] = None

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
    def split_flow_cell_name(self) -> List[str]:
        """Return split flow cell name."""
        return self.path.name.split("_")

    @property
    def full_name(self) -> str:
        """Return flow cell full name."""
        return self.path.name

    @property
    def sample_sheet_path(self) -> Path:
        """
        Return sample sheet path.
        """
        return Path(self.path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME.value)

    def set_sample_sheet_path_hk(self, hk_path: Path):
        self._sample_sheet_path_hk = hk_path

    def get_sample_sheet_path_hk(self) -> Path:
        if not self._sample_sheet_path_hk:
            raise FlowCellError("Attribute _sample_sheet_path_hk has not been assigned yet")
        return self._sample_sheet_path_hk

    @property
    def sample_type(
        self,
    ) -> Union[Type[FlowCellSampleBcl2Fastq], Type[FlowCellSampleBCLConvert]]:
        """Return the sample class used in the flow cell."""
        if self.bcl_converter == BclConverter.BCL2FASTQ:
            return FlowCellSampleBcl2Fastq
        return FlowCellSampleBCLConvert

    @property
    def sequencer_type(
        self,
    ) -> Literal[Sequencers.HISEQX, Sequencers.HISEQGA, Sequencers.NOVASEQ, Sequencers.NOVASEQX]:
        """Return the sequencer type."""
        return sequencer_types[self.machine_name]

    def get_bcl_converter(self, bcl_converter: str) -> str:
        """
        Return the BCL converter to use.
        Tries to get the BCL converter from the sequencer type if not provided.
        Note: bcl_converter can be used to override automatic selection.
        Reason: Data reproducability.
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

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists."""
        LOG.info("Check if sample sheet exists")
        return self.sample_sheet_path.exists()

    def validate_sample_sheet(self) -> bool:
        """Validate if sample sheet is on correct format."""
        try:
            get_sample_sheet_from_file(
                infile=self.sample_sheet_path,
                flow_cell_sample_type=self.sample_type,
            )
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
        return get_sample_sheet_from_file(
            infile=self._sample_sheet_path_hk,
            flow_cell_sample_type=self.sample_type,
        )

    def get_sample_sheet(self) -> SampleSheet:
        """Return sample sheet object."""
        return get_sample_sheet_from_file(
            infile=self.sample_sheet_path,
            flow_cell_sample_type=self.sample_type,
        )

    def __str__(self):
        return f"FlowCell(path={self.path},run_parameters_path={self.run_parameters_path})"
