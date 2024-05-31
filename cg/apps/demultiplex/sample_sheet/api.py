import logging
from pathlib import Path

import click

from cg.apps.demultiplex.sample_sheet.read_sample_sheet import get_flow_cell_samples_from_content
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import SampleSheetCreator
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
from cg.exc import FlowCellError, HousekeeperFileMissingError, SampleSheetError
from cg.io.controller import ReadFile, WriteFile, WriteStream
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
    delete_sample_sheet_from_housekeeper,
)
from cg.models.illumina_run_directory_data.illumina_run_directory import (
    IlluminaRunDirectory,
)
from cg.utils.files import get_directories_in_path, link_or_overwrite_file

LOG = logging.getLogger(__name__)


class SampleSheetAPI:
    """Sample Sheet API class."""

    def __init__(self, flow_cell_dir: str, hk_api: HousekeeperAPI, lims_api: LimsAPI) -> None:
        self.sequencing_runs_dir = Path(flow_cell_dir)
        self.hk_api: HousekeeperAPI = hk_api
        self.lims_api: LimsAPI = lims_api
        self.dry_run: bool = False
        self.force: bool = False
        self.validator = SampleSheetValidator()

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run

    def set_force(self, force: bool) -> None:
        """Set force."""
        LOG.debug(f"Set force to {force}")
        self.force = force

    def _get_sequencing_run(self, run_name: str) -> IlluminaRunDirectory:
        """
        Return a flow cell given a path.
        Raises:
            SampleSheetError: If the flow cell directory or the data it contains is not valid.
        """
        sequencing_run_path: Path = Path(self.sequencing_runs_dir, run_name)
        if not sequencing_run_path.exists():
            message: str = f"Could not find run for {sequencing_run_path}"
            LOG.warning(message)
            raise SampleSheetError(message)
        try:
            run_dir = IlluminaRunDirectory(sequencing_run_path)
        except FlowCellError as error:
            raise SampleSheetError from error
        return run_dir

    def validate_sample_sheet(self, sample_sheet_path: Path) -> None:
        """Return the sample sheet path if it exists and if it passes validation.
        Raises:
            SampleSheetError: If the sample sheet does not exist or does not pass validation.
        """
        if not (sample_sheet_path and sample_sheet_path.exists()):
            message: str = f"Sample sheet with path {sample_sheet_path} does not exist"
            LOG.error(message)
            raise SampleSheetError(message)
        sample_sheet_content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=sample_sheet_path
        )
        self.validator.validate_sample_sheet_from_content(sample_sheet_content)

    @staticmethod
    def _are_necessary_files_in_flow_cell(sequencing_run_dir: IlluminaRunDirectory) -> bool:
        """Determine if the flow cell has a Run Parameters file and a sample sheet."""
        try:
            sequencing_run_dir.run_parameters_path.exists()
        except FlowCellError:
            LOG.error(
                f"Run parameters file for flow cell {sequencing_run_dir.full_name} does not exist"
            )
            return False
        if not sequencing_run_dir.sample_sheet_path.exists():
            LOG.error(f"Sample sheet for flow cell {sequencing_run_dir.full_name} does not exist")
            return False
        return True

    @staticmethod
    def _replace_sample_header(sample_sheet_content: list[list[str]]) -> list[list[str]]:
        """
        Replace the old sample ID header in the Bcl2Fastq sample sheet content with the BCLConvert
        formatted one.
        Raises:
            SampleSheetError: If the data header is not found in the sample sheet.
        """
        for line in sample_sheet_content:
            if SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value in line:
                idx = line.index(
                    SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value
                )
                line[idx] = SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID.value
                return sample_sheet_content
        raise SampleSheetError("Could not find BCL2FASTQ data header in sample sheet")

    def translate_sample_sheet(self, sequencing_run_name: str) -> None:
        """Translate a Bcl2Fastq sample sheet to a BCLConvert sample sheet."""
        run_dir: IlluminaRunDirectory = self._get_sequencing_run(sequencing_run_name)
        if not self._are_necessary_files_in_flow_cell(run_dir):
            raise SampleSheetError("Could not translate sample sheet")
        original_content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=run_dir.sample_sheet_path
        )
        content_with_fixed_header: list[list[str]] = self._replace_sample_header(original_content)

        flow_cell_samples: list[FlowCellSample] = get_flow_cell_samples_from_content(
            sample_sheet_content=content_with_fixed_header
        )
        bcl_convert_creator = SampleSheetCreator(
            sequencing_run=run_dir, lims_samples=flow_cell_samples
        )
        new_content = bcl_convert_creator.construct_sample_sheet()
        self.validator.validate_sample_sheet_from_content(new_content)
        if self.dry_run:
            click.echo(
                WriteStream.write_stream_from_content(
                    file_format=FileFormat.CSV, content=new_content
                )
            )
            return
        WriteFile.write_file_from_content(
            content=new_content,
            file_format=FileFormat.CSV,
            file_path=run_dir.sample_sheet_path,
        )

    def _use_sample_sheet_from_housekeeper(self, sequencing_run: IlluminaRunDirectory) -> None:
        """
        Copy the sample sheet from Housekeeper to the flow cell directory if it exists and is valid.
        """
        try:
            sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(sequencing_run.id)
        except HousekeeperFileMissingError:
            raise SampleSheetError(
                f"Sample sheet for flow cell {sequencing_run.id} does not exist in Housekeeper"
            )
        self.validate_sample_sheet(sample_sheet_path)
        LOG.info("Sample sheet from Housekeeper is valid. Copying it to flow cell directory")
        if not self.dry_run:
            link_or_overwrite_file(src=sample_sheet_path, dst=sequencing_run.sample_sheet_path)

    def _use_sequencing_run_sample_sheet(self, sequencing_run: IlluminaRunDirectory) -> None:
        """Use the sample sheet from the flow cell directory if it is valid."""
        self.validate_sample_sheet(sequencing_run.sample_sheet_path)
        LOG.info("Sample sheet from flow cell directory is valid. Adding it to Housekeeper")
        if not self.dry_run:
            try:
                delete_sample_sheet_from_housekeeper(
                    flow_cell_id=sequencing_run.id, hk_api=self.hk_api
                )
            except HousekeeperFileMissingError:
                pass
            add_and_include_sample_sheet_path_to_housekeeper(
                flow_cell_directory=sequencing_run.path,
                flow_cell_name=sequencing_run.id,
                hk_api=self.hk_api,
            )

    def _get_sample_sheet_content(self, sequencing_run: IlluminaRunDirectory) -> list[list[str]]:
        """Return the sample sheet content for a flow cell."""
        lims_samples: list[FlowCellSample] = list(
            get_flow_cell_samples(
                lims=self.lims_api,
                sequencing_run_id=sequencing_run.id,
            )
        )
        if not lims_samples:
            message: str = f"Could not find any samples in LIMS for {sequencing_run.id}"
            LOG.warning(message)
            raise SampleSheetError(message)
        creator = SampleSheetCreator(sequencing_run=sequencing_run, lims_samples=lims_samples)
        LOG.info(
            f"Constructing sample sheet for the {sequencing_run.sequencer_type} flow cell {sequencing_run.id}"
        )
        return creator.construct_sample_sheet()

    def _create_sample_sheet_file(self, sequencing_run: IlluminaRunDirectory) -> None:
        """Create a valid sample sheet in the flow cell directory and add it to Housekeeper."""
        sample_sheet_content: list[list[str]] = self._get_sample_sheet_content(sequencing_run)
        if not self.force:
            self.validator.validate_sample_sheet_from_content(sample_sheet_content)
        LOG.info(f"Writing sample sheet to {sequencing_run.sample_sheet_path.resolve()}")
        if self.dry_run:
            click.echo(
                WriteStream.write_stream_from_content(
                    file_format=FileFormat.CSV, content=sample_sheet_content
                )
            )
            return
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=sequencing_run.sample_sheet_path,
        )
        try:
            delete_sample_sheet_from_housekeeper(flow_cell_id=sequencing_run.id, hk_api=self.hk_api)
        except HousekeeperFileMissingError:
            pass
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=sequencing_run.path,
            flow_cell_name=sequencing_run.id,
            hk_api=self.hk_api,
        )

    def get_or_create_sample_sheet(self, sequencing_run_name: str) -> None:
        """
        Ensure that a valid sample sheet is present in the flow cell directory by fetching it from
        housekeeper or creating it if there is not a valid sample sheet.
        """
        sequencing_run: IlluminaRunDirectory = self._get_sequencing_run(sequencing_run_name)
        LOG.info("Fetching and validating sample sheet from Housekeeper")
        try:
            self._use_sample_sheet_from_housekeeper(sequencing_run)
            return
        except SampleSheetError:
            LOG.warning(
                "It was not possible to use sample sheet from Housekeeper, "
                "trying sequencing run sample sheet"
            )
        try:
            self._use_sequencing_run_sample_sheet(sequencing_run)
            return
        except SampleSheetError:
            LOG.warning(
                "It was not possible to use sample sheet from the sequencing run, creating new sample sheet"
            )
        self._create_sample_sheet_file(sequencing_run)

    def get_or_create_all_sample_sheets(self):
        """Ensure that a valid sample sheet is present in all flow cell directories."""
        for sequencing_run_dir in get_directories_in_path(self.sequencing_runs_dir):
            try:
                self.get_or_create_sample_sheet(sequencing_run_dir.name)
            except Exception as error:
                LOG.error(f"Could not create sample sheet for {sequencing_run_dir.name}: {error}")
                continue
