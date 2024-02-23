import logging
from pathlib import Path

import click

from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet_content
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.constants import FileFormat
from cg.exc import FlowCellError, HousekeeperFileMissingError, SampleSheetError
from cg.io.controller import WriteFile, WriteStream
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
    delete_sample_sheet_from_housekeeper,
)
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.utils.files import get_directories_in_path, link_or_overwrite_file

LOG = logging.getLogger(__name__)


class SampleSheetAPI:
    """Sample Sheet API class."""

    def __init__(self, flow_cell_dir: str, hk_api: HousekeeperAPI, lims_api: LimsAPI) -> None:
        self.flow_cell_runs_dir = Path(flow_cell_dir)
        self.hk_api: HousekeeperAPI = hk_api
        self.lims_api: LimsAPI = lims_api
        self.dry_run: bool = False
        self.force: bool = False
        self.validator = SampleSheetValidator()
        self.bcl_converter: str | None = None

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run

    def set_force(self, force: bool) -> None:
        """Set force."""
        LOG.debug(f"Set force to {force}")
        self.force = force

    def _get_flow_cell(
        self, flow_cell_name: str, bcl_converter: str | None
    ) -> FlowCellDirectoryData:
        """
        Return a flow cell given a path and the bcl converter.
        Raises:
            SampleSheetError: If the flow cell directory or the data it contains is not valid.
        """
        flow_cell_path: Path = Path(self.flow_cell_runs_dir, flow_cell_name)
        if not flow_cell_path.exists():
            message: str = f"Could not find flow cell {flow_cell_path}"
            LOG.warning(message)
            raise SampleSheetError(message)
        try:
            flow_cell = FlowCellDirectoryData(
                flow_cell_path=flow_cell_path, bcl_converter=bcl_converter
            )
        except FlowCellError as error:
            raise SampleSheetError from error
        return flow_cell

    def validate_sample_sheet(
        self, sample_sheet_path: Path, bcl_converter: str | None = None
    ) -> None:
        """Return the sample sheet path if it exists and if it passes validation.
        Raises:
            SampleSheetError: If the sample sheet does not exist or does not pass validation.
        """
        if not (sample_sheet_path and sample_sheet_path.exists()):
            message: str = f"Sample sheet with path {sample_sheet_path} does not exist"
            LOG.error(message)
            raise SampleSheetError(message)
        self.validator.validate_sample_sheet_from_file(
            file_path=sample_sheet_path, bcl_converter=bcl_converter
        )

    def _use_sample_sheet_from_housekeeper(self, flow_cell: FlowCellDirectoryData) -> None:
        """
        Copy the sample sheet from Housekeeper to the flow cell directory if it exists and is valid.
        """
        try:
            sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(flow_cell.id)
        except HousekeeperFileMissingError:
            raise SampleSheetError(
                f"Sample sheet for flow cell {flow_cell.id} does not exist in Housekeeper"
            )
        self.validate_sample_sheet(
            sample_sheet_path=sample_sheet_path, bcl_converter=self.bcl_converter
        )
        LOG.info("Sample sheet from Housekeeper is valid. Copying it to flow cell directory")
        if not self.dry_run:
            link_or_overwrite_file(src=sample_sheet_path, dst=flow_cell.sample_sheet_path)

    def _use_flow_cell_sample_sheet(self, flow_cell: FlowCellDirectoryData) -> None:
        """Use the sample sheet from the flow cell directory if it is valid."""
        self.validate_sample_sheet(
            sample_sheet_path=flow_cell.sample_sheet_path, bcl_converter=self.bcl_converter
        )
        LOG.info("Sample sheet from flow cell directory is valid. Adding it to Housekeeper")
        if not self.dry_run:
            try:
                delete_sample_sheet_from_housekeeper(flow_cell_id=flow_cell.id, hk_api=self.hk_api)
            except HousekeeperFileMissingError:
                pass
            add_and_include_sample_sheet_path_to_housekeeper(
                flow_cell_directory=flow_cell.path,
                flow_cell_name=flow_cell.id,
                hk_api=self.hk_api,
            )

    def _get_sample_sheet_content(self, flow_cell: FlowCellDirectoryData) -> list[list[str]]:
        """Return the sample sheet content for a flow cell."""
        lims_samples: list[FlowCellSample] = list(
            get_flow_cell_samples(
                lims=self.lims_api,
                flow_cell_id=flow_cell.id,
                flow_cell_sample_type=flow_cell.sample_type,
            )
        )
        if not lims_samples:
            message: str = f"Could not find any samples in LIMS for {flow_cell.id}"
            LOG.warning(message)
            raise SampleSheetError(message)
        return create_sample_sheet_content(flow_cell=flow_cell, lims_samples=lims_samples)

    def _create_sample_sheet_file(self, flow_cell: FlowCellDirectoryData) -> None:
        """Create a valid sample sheet in the flow cell directory and add it to Housekeeper."""
        sample_sheet_content: list[list[str]] = self._get_sample_sheet_content(flow_cell)
        if not self.force:
            self.validator.validate_sample_sheet_from_content(
                content=sample_sheet_content, bcl_convert=flow_cell.bcl_converter
            )
        LOG.info(f"Writing sample sheet to {flow_cell.sample_sheet_path.resolve()}")
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
            file_path=flow_cell.sample_sheet_path,
        )
        try:
            delete_sample_sheet_from_housekeeper(flow_cell_id=flow_cell.id, hk_api=self.hk_api)
        except HousekeeperFileMissingError:
            pass
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=flow_cell.path, flow_cell_name=flow_cell.id, hk_api=self.hk_api
        )

    def get_or_create_sample_sheet(self, flow_cell_name: str, bcl_converter: str | None) -> None:
        """
        Ensure that a valid sample sheet is present in the flow cell directory by fetching it from
        housekeeper or creating it if there is not a valid sample sheet.
        """
        self.bcl_converter = bcl_converter
        flow_cell: FlowCellDirectoryData = self._get_flow_cell(
            flow_cell_name=flow_cell_name, bcl_converter=bcl_converter
        )
        LOG.info("Fetching and validating sample sheet from Housekeeper")
        try:
            self._use_sample_sheet_from_housekeeper(flow_cell)
            return
        except SampleSheetError:
            LOG.warning(
                "It was not possible to use sample sheet from Housekeeper, "
                "trying flow cell sample sheet"
            )
        try:
            self._use_flow_cell_sample_sheet(flow_cell)
            return
        except SampleSheetError:
            LOG.warning(
                "It was not possible to use sample sheet from flow cell, creating new sample sheet"
            )
        self._create_sample_sheet_file(flow_cell)

    def get_or_create_all_sample_sheets(self):
        """Ensure that a valid sample sheet is present in all flow cell directories."""
        for flow_cell_dir in get_directories_in_path(self.flow_cell_runs_dir):
            try:
                self.get_or_create_sample_sheet(
                    flow_cell_name=flow_cell_dir.name, bcl_converter=None
                )
            except Exception as error:
                LOG.error(f"Could not create sample sheet for {flow_cell_dir.name}: {error}")
                continue
