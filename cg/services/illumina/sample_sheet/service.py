import logging
from pathlib import Path

from cg.apps.demultiplex.sample_sheet.utils import (
    add_and_include_sample_sheet_path_to_housekeeper,
    delete_sample_sheet_from_housekeeper,
)
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.sample_sheet.creator import SampleSheetCreator
from cg.services.illumina.sample_sheet.parser import SampleSheetParser
from cg.services.illumina.sample_sheet.translator import SampleSheetTranslator
from cg.services.illumina.sample_sheet.validator import SampleSheetValidator
from cg.utils.files import get_directories_in_path, link_or_overwrite_file

LOG = logging.getLogger(__name__)


class IlluminaSampleSheetService:
    def __init__(
        self,
        sequencing_dir: str,
        hk_api: HousekeeperAPI,
        creator: SampleSheetCreator,
        parser: SampleSheetParser,
        translator: SampleSheetTranslator,
        validator: SampleSheetValidator,
    ):
        self.sequencing_dir = Path(sequencing_dir)
        self.hk_api = hk_api
        self.creator = creator
        self.parser = parser
        self.translator = translator
        self.validator = validator

    # TODO: Add fetching from HK and FC dir
    def create(self, sequencing_run_name: str) -> None:
        """Write a sample sheet for a flow cell."""
        run_dir: IlluminaRunDirectoryData = self._get_illumina_run_dir_data(sequencing_run_name)
        if self._use_sample_sheet_from_hk(run_dir_data=run_dir):
            return
        if self._use_sample_sheet_from_sequencing_dir(run_dir_data=run_dir):
            return
        LOG.debug(f"Creating a new sample sheet for sequencing run {sequencing_run_name}")
        sample_sheet_content: list[list[str]] = self.creator.create(run_dir).get_content()
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=run_dir.sample_sheet_path,
        )

    def create_all(self):
        for run_dir_path in get_directories_in_path(self.sequencing_dir):
            LOG.info(f"Getting a valid sample sheet for run {run_dir_path.name}")
            try:
                self.create(run_dir_path.name)
                LOG.info(f"Got a valid sample sheet for run {run_dir_path.name}")
            except Exception as error:
                LOG.error(
                    f"Could not find or create valid sample sheet for {run_dir_path.name}: {error}"
                )
                continue

    def translate(self, sequencing_run_name: str) -> None:
        run_dir_data: IlluminaRunDirectoryData = self._get_illumina_run_dir_data(
            sequencing_run_name
        )
        if not self._are_necessary_files_in_flow_cell(run_dir_data):
            raise MissingFilesError("Missing necessary files in run directory for translation")
        content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=run_dir_data.sample_sheet_path
        )
        if not self.validator.is_sample_sheet_bcl2fastq():
            LOG.error("Sample sheet is already in version 2")
            return
        self.translator.translate_content()

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

    # TODO add decorator to catch HousekeeperFileMissingError and validation errors, add logs and return False
    def _use_sample_sheet_from_hk(self, run_dir_data: IlluminaRunDirectoryData) -> bool:
        """Get the sample sheet content from Housekeeper."""

        sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(run_dir_data.id)
        run_dir_data.set_sample_sheet_path_hk(sample_sheet_path)
        self.validator.validate_file(file_path=sample_sheet_path)
        if self.dry_run:
            LOG.info(
                "Sample sheet from Housekeeper is valid, "
                "would have copied it to sequencing run directory"
            )
            return True
        LOG.info("Sample sheet from Housekeeper is valid. Copying it to sequencing run directory")
        link_or_overwrite_file(src=sample_sheet_path, dst=run_dir_data.sample_sheet_path)
        return True

    # TODO add decorator to catch HousekeeperFileMissingError and validation errors, add logs and return False
    def _use_sample_sheet_from_sequencing_dir(self, run_dir_data: IlluminaRunDirectoryData) -> bool:
        """Get the sample sheet content from the flow cell directory."""
        self.validator.validate_file(run_dir_data.sample_sheet_path)
        if self.dry_run:
            LOG.info(
                "Sample sheet from sequencing run directory is valid, "
                "would have added it to Housekeeper"
            )
            return True
        LOG.info("Sample sheet from sequencing run directory is valid. Adding it to Housekeeper")
        try:
            delete_sample_sheet_from_housekeeper(flow_cell_id=run_dir_data.id, hk_api=self.hk_api)
        except HousekeeperFileMissingError:
            pass
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=run_dir_data.path,
            flow_cell_name=run_dir_data.id,
            hk_api=self.hk_api,
        )
        return True
