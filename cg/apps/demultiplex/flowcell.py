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
        LOG.info("Instantiating Flowcell with path %s", flowcell_path)
        self.path = flowcell_path
        LOG.info("Set flowcell id to %s", self.flowcell_id)
        self._flowcell_id: Optional[str] = None
        self._run_parameters: Optional[RunParameters] = None

    @property
    def flowcell_id(self) -> str:
        if not self._flowcell_id:
            base_name: str = self.path.name.split("_")[-1]
            self._flowcell_id = base_name[1:]
        return self._flowcell_id

    @property
    def sample_sheet_path(self) -> Path:
        return Path(self.path, "SampleSheet.csv")

    @property
    def run_parameters_path(self) -> Path:
        return self.path / "runParameters.xml"

    @property
    def run_parameters_object(self) -> RunParameters:
        if not self.run_parameters_path.exists():
            raise FileNotFoundError(
                f"Could not find run parameters file {self.run_parameters_path}"
            )
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
    def demultiplexing_ongoing_path(self) -> Path:
        return Path(self.path, "demuxstarted.txt")

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists"""
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
        return self.rta_complete_path.exists()

    def is_copy_completed(self) -> bool:
        """Check if copy of flowcell is done

        This is indicated by that the file CopyComplete.txt exists
        """
        return self.copy_complete_path.exists()

    def is_demultiplexing_ongoing(self) -> bool:
        """Check if demultiplexing is ongoing

        This is indicated by if the file demuxstarted.txt exists (?)
        """
        return self.demultiplexing_ongoing_path.exists()

    def is_flowcell_ready(self) -> bool:
        """Check if a flowcell is ready for demultiplexing

        A flowcell is ready if the two files RTAComplete.txt and CopyComplete.txt exists in the flowcell directory
        """
        if not self.is_sequencing_done():
            LOG.info("Sequencing is not completed for flowcell %s", self.flowcell_id)
            return False

        if not self.is_copy_completed():
            LOG.info("Copy of sequence data is not ready for flowcell %s", self.flowcell_id)
            return False

        LOG.info("Flowcell %s is ready for demultiplexing", self.flowcell_id)
        return True

    def is_demultiplexing_possible(self) -> bool:
        """Check if it is possible to start demultiplexing

        This means that
            - flowcell should be ready for demultiplexing (all files in place)
            - sample sheet needs to exist
            - demultiplexing should not be running
        """
        if not self.is_flowcell_ready():
            return False
        if not self.sample_sheet_exists():
            LOG.warning("Could not find sample sheet for %s", self.flowcell_id)
            return False
        if self.is_demultiplexing_ongoing():
            LOG.warning("Demultiplexing is ongoing for %s", self.flowcell_id)
            return False
        return True

    def __str__(self):
        return f"Flowcell(path={self.path},run_parameters_path={self.run_parameters_path})"
