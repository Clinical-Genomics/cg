import logging
import os
from pathlib import Path

from cg.apps.demultiplex.sample_sheet.create import create_sample_sheet
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.lims.sample_sheet import get_flow_cell_samples
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import BclConverter
from cg.exc import FlowCellError, HousekeeperFileMissingError, SampleSheetError
from cg.io.controller import ReadFile, WriteFile
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


class SampleSheetAPI:
    """Sample Sheet API class."""

    def __init__(self, config: CGConfig) -> None:
        self.config: CGConfig = config
        self.flow_cell_runs_dir = Path(config.illumina_flow_cells_directory)
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.dry_run: bool = False
        self.force: bool = False

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
            LOG.warning(f"Could not find flow cell {flow_cell_path}")
            raise SampleSheetError(f"Could not find flow cell {flow_cell_path}")
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
                self.validate_from_path(sample_sheet_path)
            except SampleSheetError:
                LOG.warning(f"Sample sheet {sample_sheet_path} was not valid")
                return
        return sample_sheet_path

    def get_valid_sample_sheet_path_from_hk(self, flow_cell_id: str) -> Path | None:
        """Return the sample sheet path from Housekeeper if is valid and exists."""
        try:
            sample_sheet_path: Path | None = self.hk_api.get_sample_sheet_path(flow_cell_id)
        except HousekeeperFileMissingError:
            LOG.warning(f"Sample sheet for flow cell {flow_cell_id} not found in Housekeeper")
            return
        return self.get_valid_sample_sheet_path(sample_sheet_path)

    def validate_from_content(self, content: list[list[str]]) -> None:
        """
        Validate a sample sheet given its content.
        Raises:
            SampleSheetError: If the sample sheet is not valid.
        """
        pass

    def validate_from_path(self, path: Path) -> None:
        """
        Validate a sample sheet given the path to the file.
        Raises:
            SampleSheetError: If the sample sheet is not valid.
        """
        content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=path
        )
        self.validate_from_content(content)

    def create_sample_sheet_content(self, flow_cell: FlowCellDirectoryData) -> list[list[str]]:
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
        return create_sample_sheet(flow_cell=flow_cell, lims_samples=lims_samples)

    def create_sample_sheet(self, flow_cell: FlowCellDirectoryData) -> None:
        """Create a valid sample sheet in the flow cell directory and add it to Housekeeper."""
        sample_sheet_content: list[list[str]] = self.create_sample_sheet_content(flow_cell)
        if not self.force:
            self.validate_from_content(sample_sheet_content)
        WriteFile.write_file_from_content(
            content=sample_sheet_content,
            file_format=FileFormat.CSV,
            file_path=flow_cell.sample_sheet_path,
        )
        # TODO: REPLACE FOR ADDING AND INCLUDING TO HK

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
            LOG.debug(
                "Sample sheet already exists in Housekeeper. Hard-linking it to flow cell directory"
            )
            if not self.dry_run:
                os.link(src=hk_sample_sheet_path, dst=flow_cell.sample_sheet_path)
            return
        elif self.get_valid_sample_sheet_path(flow_cell.sample_sheet_path):
            LOG.info("Sample sheet already exists in flow cell directory")
            if not self.dry_run:
                # TODO: REPLACE FOR ADDING AND INCLUDING TO HK
                return
        else:
            self.create_sample_sheet(flow_cell)

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
