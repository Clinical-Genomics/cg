import datetime
import logging
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError
from typing_extensions import Literal

from cg.exc import FlowcellError
from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import SampleSheet, get_sample_sheet_from_file
from cgmodels.exceptions import SampleSheetError

LOG = logging.getLogger(__name__)


class Flowcell:
    """Class to collect information about flowcell directories and there particular files"""

    def __init__(self, flowcell_path: Path, bcl_converter: Optional[str] = "bcl2fastq"):
        LOG.debug("Instantiating Flowcell with path %s", flowcell_path)
        self.path = flowcell_path
        self.bcl_converter: Optional[str] = bcl_converter
        self._run_parameters: Optional[RunParameters] = None
        self.run_date: datetime.datetime = datetime.datetime.now()
        self.machine_name: str = ""
        self.machine_number: int = 0
        # Base name is flowcell-id + flowcell position
        self.base_name: str = ""
        self.flowcell_id: str = ""
        self.flowcell_position: Literal["A", "B"] = "A"
        self.parse_flowcell_name()

    def parse_flowcell_name(self):
        """Parse relevant information from flowcell name

        This will assume that the flowcell naming convention is used. If not we skip the flowcell.
        Convention is: <date>_<machine>_<run_numbers>_<A|B><flowcell_id>
        Example: 201203_A00689_0200_AHVKJCDRXX
        """
        split_name: List[str] = self.path.name.split("_")
        if len(split_name) != 4:
            message = f"Flowcell {self.path.name} does not follow the flowcell naming convention"
            LOG.warning(message)
            raise FlowcellError(message)
        self.run_date = datetime.datetime.strptime(split_name[0], "%y%m%d")
        self.machine_name = split_name[1]
        self.machine_number = int(split_name[2])
        base_name: str = split_name[-1]
        self.base_name = base_name
        LOG.debug("Set flowcell id to %s", base_name)
        self.flowcell_id = base_name[1:]
        self.flowcell_position = base_name[0]

    @property
    def flowcell_full_name(self) -> str:
        return self.path.name

    @property
    def sample_sheet_path(self) -> Path:
        return self.path / "SampleSheet.csv"

    @property
    def run_parameters_path(self) -> Path:
        return self.path / "RunParameters.xml"

    @property
    def run_parameters_object(self) -> RunParameters:
        if not self.run_parameters_path.exists():
            message = f"Could not find run parameters file {self.run_parameters_path}"
            LOG.warning(message)
            raise FileNotFoundError(message)
        if not self._run_parameters:
            self._run_parameters = RunParameters(run_parameters_path=self.run_parameters_path)
        return self._run_parameters

    @property
    def rta_complete_path(self) -> Path:
        return Path(self.path, "RTAComplete.txt")

    @property
    def copy_complete_path(self) -> Path:
        return Path(self.path, "CopyComplete.txt")

    @property
    def demultiplexing_started_path(self) -> Path:
        return Path(self.path, "demuxstarted.txt")

    @property
    def trailblazer_config_path(self) -> Path:
        return Path(self.path, "slurm_job_ids.yaml")

    def is_demultiplexing_started(self) -> bool:
        """Create the path to where the demuliplexed result should be produced"""
        return self.demultiplexing_started_path.exists()

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists"""
        LOG.info("Check if sample sheet exists")
        return self.sample_sheet_path.exists()

    def validate_sample_sheet(self) -> bool:
        """Validate if sample sheet is on correct format"""
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
        return get_sample_sheet_from_file(
            infile=self.sample_sheet_path, sheet_type="S4", bcl_converter=self.bcl_converter
        )

    def is_sequencing_done(self) -> bool:
        """Check if sequencing is done

        This is indicated by that the file RTAComplete.txt exists
        """
        LOG.info("Check if sequencing is done")
        return self.rta_complete_path.exists()

    def is_copy_completed(self) -> bool:
        """Check if copy of flowcell is done

        This is indicated by that the file CopyComplete.txt exists
        """
        LOG.info("Check if copy of data from sequence instrument is ready")
        return self.copy_complete_path.exists()

    def is_flowcell_ready(self) -> bool:
        """Check if a flowcell is ready for demultiplexing

        A flowcell is ready if the two files RTAComplete.txt and CopyComplete.txt exists in the
        flowcell directory
        """
        LOG.info("Check if flowcell is ready for demultiplexing")
        if not self.is_sequencing_done():
            LOG.info("Sequencing is not completed for flowcell %s", self.flowcell_id)
            return False
        LOG.debug("Sequence is done for flowcell %s", self.flowcell_id)
        if not self.is_copy_completed():
            LOG.info("Copy of sequence data is not ready for flowcell %s", self.flowcell_id)
            return False
        LOG.debug("All data has been transferred for flowcell %s", self.flowcell_id)
        LOG.info("Flowcell %s is ready for demultiplexing", self.flowcell_id)
        return True

    def __str__(self):
        return f"Flowcell(path={self.path},run_parameters_path={self.run_parameters_path})"
