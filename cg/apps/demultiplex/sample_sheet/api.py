import logging
import os
from pathlib import Path

import click
from pydantic import ValidationError

from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet_content
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import BclConverter
from cg.exc import FlowCellError, HousekeeperFileMissingError, SampleSheetError
from cg.io.controller import WriteFile, WriteStream
from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
)
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

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

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run

    def set_force(self, force: bool) -> None:
        """Set force."""
        LOG.debug(f"Set force to {force}")
        self.force = force

    def get_flow_cell(self, flow_cell_name: str, bcl_converter: str) -> FlowCellDirectoryData:
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

    def get_valid_sample_sheet_path(self, sample_sheet_path: Path) -> Path | None:
        """Return the sample sheet path if it exists and if it passes validation."""
        if sample_sheet_path and sample_sheet_path.exists():
            try:
                self.validator.validate_sample_sheet_from_file(sample_sheet_path)
            except (SampleSheetError, ValidationError):
                LOG.warning(f"Sample sheet {sample_sheet_path} was not valid")
                return
            return sample_sheet_path
        else:
            LOG.warning(f"Sample sheet with path {sample_sheet_path} does not exist")
            return

    def get_valid_sample_sheet_path_from_hk(self, flow_cell_id: str) -> Path | None:
        """Return the sample sheet path from Housekeeper if is valid and exists."""
        try:
            sample_sheet_path: Path | None = self.hk_api.get_sample_sheet_path(flow_cell_id)
        except HousekeeperFileMissingError:
            LOG.warning(f"Sample sheet for flow cell {flow_cell_id} not found in Housekeeper")
            return
        return self.get_valid_sample_sheet_path(sample_sheet_path)

    def get_sample_sheet_content(self, flow_cell: FlowCellDirectoryData) -> list[list[str]]:
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

    def create_sample_sheet_file(self, flow_cell: FlowCellDirectoryData) -> None:
        """Create a valid sample sheet in the flow cell directory and add it to Housekeeper."""
        sample_sheet_content: list[list[str]] = self.get_sample_sheet_content(flow_cell)
        if not self.force:
            self.validator.validate_sample_sheet_from_content(sample_sheet_content)
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
        add_and_include_sample_sheet_path_to_housekeeper(
            flow_cell_directory=flow_cell.path, flow_cell_name=flow_cell.id, hk_api=self.hk_api
        )

    def validate(self, sample_sheet_path: Path) -> None:
        """Validate a sample sheet."""
        self.validator.validate_sample_sheet_from_file(sample_sheet_path)

    def get_or_create_sample_sheet(self, flow_cell_name: str, bcl_converter: str) -> None:
        """
        Ensure that a valid sample sheet is present in the flow cell directory.
        If a valid sample sheet for the flow cell is present in Housekeeper, the function hard-links
        it to the flow cell directory. If not and if the flow cell directory has a valid sample
        sheet, the function adds and includes it to Housekeeper. If neither is present, the
        function creates a sample sheet for the flow cell and adds and includes it to Housekeeper.
        """
        flow_cell: FlowCellDirectoryData = self.get_flow_cell(
            flow_cell_name=flow_cell_name, bcl_converter=bcl_converter
        )
        if hk_sample_sheet_path := self.get_valid_sample_sheet_path_from_hk(flow_cell.id):
            LOG.info(
                "Sample sheet already exists in Housekeeper. Hard-linking it to flow cell directory"
            )
            if not self.dry_run:
                os.link(src=hk_sample_sheet_path, dst=flow_cell.sample_sheet_path)
        elif self.get_valid_sample_sheet_path(flow_cell.sample_sheet_path):
            LOG.info("Sample sheet already exists in flow cell directory. Adding to Housekeeper")
            if not self.dry_run:
                add_and_include_sample_sheet_path_to_housekeeper(
                    flow_cell_directory=flow_cell.path,
                    flow_cell_name=flow_cell.id,
                    hk_api=self.hk_api,
                )
        else:
            LOG.info(f"Creating new sample sheet for flow cell {flow_cell_name}")
            self.create_sample_sheet_file(flow_cell)

    def get_or_create_all_sample_sheets(self):
        """Ensure that a valid sample sheet is present in all flow cell directories."""
        for flow_cell_dir in self.flow_cell_runs_dir.iterdir():
            try:
                self.get_or_create_sample_sheet(
                    flow_cell_dir.name, bcl_converter=BclConverter.BCL2FASTQ
                )
            except Exception as error:
                LOG.error(f"Could not create sample sheet for {flow_cell_dir.name}: {error}")
                continue
