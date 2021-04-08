import logging
from pathlib import Path
from typing import Optional

from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import get_sample_sheet_from_file
from cgmodels.exceptions import SampleSheetError
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


class Flowcell:
    """Class to collect information about flowcell directories and there particular files"""

    def __init__(self, flowcell_path: Path):
        LOG.debug("Instantiating Flowcell with path %s", flowcell_path)
        self.path = flowcell_path
        LOG.debug("Set flowcell id to %s", self.flowcell_id)
        self._run_parameters: Optional[RunParameters] = None

    @property
    def flowcell_id(self) -> str:
        base_name: str = self.path.name.split("_")[-1]
        return base_name[1:]

    @property
    def sample_sheet_path(self) -> Path:
        return Path(self.path, "SampleSheet.csv")

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
            get_sample_sheet_from_file(infile=self.sample_sheet_path, sheet_type="S4")
        except (SampleSheetError, ValidationError) as error:
            LOG.warning("Invalid sample sheet")
            LOG.warning(error)
            return False
        return True

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

        A flowcell is ready if the two files RTAComplete.txt and CopyComplete.txt exists in the flowcell directory
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
