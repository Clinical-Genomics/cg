import logging
from pathlib import Path

from cg.models.demultiplex.run_parameters import RunParameters
from cgmodels.demultiplex.sample_sheet import get_sample_sheet
from cgmodels.exceptions import SampleSheetError
from pydantic import ValidationError

LOG = logging.getLogger(__name__)


class Flowcell:
    """Class to collect information about flowcell directories and there particular files"""

    def __init__(self, flowcell_path: Path):
        LOG.info("Instantiating Flowcell with path %s", flowcell_path)
        self.path = flowcell_path
        LOG.info("Set flowcell id to %s", self.flowcell_id)

    @property
    def flowcell_id(self) -> str:
        base_name: str = self.path.name.split("_")[-1]
        return base_name[1:]

    @property
    def sample_sheet_path(self) -> Path:
        return Path(self.path, "SampleSheet.csv")

    def sample_sheet_exists(self) -> bool:
        """Check if sample sheet exists"""
        return self.sample_sheet_path.exists()

    def validate_sample_sheet(self) -> bool:
        """Validate if sample sheet is on correct format"""
        try:
            get_sample_sheet(infile=self.sample_sheet_path, sheet_type="S4")
        except (SampleSheetError, ValidationError) as error:
            LOG.warning("Invalid sample sheet")
            LOG.warning(error)
            return False
        return True

    @property
    def run_parameters_path(self) -> Path:
        return self.path / "runParameters.xml"

    @property
    def run_parameters_object(self) -> RunParameters:
        if not self.run_parameters_path.exists():
            raise FileNotFoundError(
                "Could not find run parameters file %s".format(self.run_parameters_path)
            )
        return RunParameters(run_parameters_path=self.run_parameters_path)

    def fetch_logfile_path(self, out_dir: Path) -> Path:
        """Create the path to the logfile"""
        return out_dir / "Unaligned" / f"project.{self.flowcell_id}.log"

    def is_sequencing_done(self) -> bool:
        """Check if sequencing is done

        This is indicated by that the file RTAComplete.txt exists
        """
        return Path(self.path, "RTAComplete.txt").exists()

    def is_copy_completed(self) -> bool:
        """Check if copy of flowcell is done

        This is indicated by that the file CopyComplete.txt exists
        """
        return Path(self.path, "CopyComplete.txt").exists()

    def is_demultiplexing_ongoing(self) -> bool:
        """Check if demultiplexing is ongoing

        This is indicated by if the file demuxstarted.txt exists (?)
        """
        return Path(self.path, "demuxstarted.txt").exists()

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

    def __str__(self):
        return f"Flowcell(path={self.path},run_parameters_path={self.run_parameters_path})"
