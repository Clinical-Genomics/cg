import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.sample_sheet.creator import SampleSheetCreator
from cg.services.illumina.sample_sheet.parser import SampleSheetParser
from cg.services.illumina.sample_sheet.validator import SampleSheetValidator
from cg.utils.files import get_directories_in_path

LOG = logging.getLogger(__name__)


class IlluminaSampleSheetService:
    def __init__(
        self,
        sequencing_dir: str,
        hk_api: HousekeeperAPI,
        creator: SampleSheetCreator,
        parser: SampleSheetParser,
        validator: SampleSheetValidator,
    ):
        self.sequencing_dir = Path(sequencing_dir)
        self.hk_api = hk_api
        self.creator = creator
        self.parser = parser
        self.validator = validator

    # TODO: Add fetching from HK and FC dir
    def create(self, sequencing_run_name: str) -> None:
        """Write a sample sheet for a flow cell."""
        run_dir: IlluminaRunDirectoryData = self._get_illumina_run_dir_data(sequencing_run_name)
        sample_sheet_content: list[list[str]] = self.creator.create(run_dir).get_content()
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=run_dir.sample_sheet_path,
        )

    def create_all(self):
        for run_dir_path in get_directories_in_path(self.sequencing_dir):
            LOG.info(f"Getting a valid sample sheet for flow cell {run_dir_path.name}")
            try:
                self.create(run_dir_path.name)
            except Exception as error:
                LOG.error(f"Could not create sample sheet for {run_dir_path.name}: {error}")
                continue

    def translate(self):
        pass

    def validate(self, sample_sheet_path: str):
        self.validator.validate_file(file_path=Path(sample_sheet_path))

    def _get_illumina_run_dir_data(self, sequencing_run: str) -> IlluminaRunDirectoryData:
        """
        Return an Illumina run directory data given the sequencing run name.
        Raises:
            SampleSheetError: If the flow cell directory or the data it contains is not valid.
        """
        run_path: Path = Path(self.sequencing_dir, sequencing_run)
        if not run_path.exists():
            message: str = f"Could not find flow cell {run_path.as_posix()}"
            LOG.warning(message)
            raise Exception(message)
        flow_cell = IlluminaRunDirectoryData(run_path)
        return flow_cell
