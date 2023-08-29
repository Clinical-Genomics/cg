"""Post-processing Demultiplex API."""
import logging
from pathlib import Path
from typing import List, Optional
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.housekeeper.hk import HousekeeperAPI


from cg.exc import FlowCellError

from cg.meta.demultiplex.housekeeper_storage_functions import (
    store_flow_cell_data_in_housekeeper,
    get_sample_sheets_from_latest_version,
)
from cg.meta.demultiplex.status_db_storage_functions import (
    store_flow_cell_data_in_status_db,
    store_sequencing_metrics_in_status_db,
    update_sample_read_counts_in_status_db,
)
from cg.meta.demultiplex.utils import (
    create_delivery_file_in_flow_cell_directory,
    parse_flow_cell_directory_data,
)
from cg.meta.demultiplex.validation import is_flow_cell_ready_for_postprocessing
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store


LOG = logging.getLogger(__name__)


class DemuxPostProcessingAPI:
    """Post demultiplexing API class."""

    def __init__(self, config: CGConfig) -> None:
        self.demux_api: DemultiplexingAPI = config.demultiplex_api
        self.status_db: Store = config.status_db
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"Set dry run to {dry_run}")
        self.dry_run = dry_run
        if dry_run:
            self.demux_api.set_dry_run(dry_run=dry_run)

    def finish_flow_cell(
        self,
        flow_cell_directory_name: str,
        bcl_converter: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Store data for the demultiplexed flow cell and mark it as ready for delivery.
        This function:
            - Stores the flow cell in the status database
            - Stores sequencing metrics in the status database
            - Updates sample read counts in the status database
            - Stores the flow cell data in the housekeeper database
            - Creates a delivery file in the flow cell directory
        Args:
            flow_cell_directory_name (str): The name of the flow cell directory to be finalized.
            bcl_converter (str): The name of the bcl converter used for demultiplexing.
            force (bool): If True, the flow cell will be finalized even when it is already marked for delivery.
        Raises:
            FlowCellError: If the flow cell directory or the data it contains is not valid.
        """
        if self.dry_run:
            LOG.info(f"Dry run will not finish flow cell {flow_cell_directory_name}")
            return

        LOG.info(f"Finish flow cell {flow_cell_directory_name}")

        flow_cell_out_directory: Path = Path(
            self.demux_api.demultiplexed_runs_dir, flow_cell_directory_name
        )
        flow_cell_run_directory: Path = Path(
            self.demux_api.flow_cells_dir, flow_cell_directory_name
        )
        parsed_flow_cell: FlowCellDirectoryData = parse_flow_cell_directory_data(
            flow_cell_directory=flow_cell_out_directory,
            bcl_converter=bcl_converter,
        )

        sample_sheet_path: Path = Path(
            get_sample_sheets_from_latest_version(
                flow_cell_id=parsed_flow_cell.id, hk_api=self.hk_api
            )[0].full_path
        )
        parsed_flow_cell.set_sample_sheet_path_hk(hk_path=sample_sheet_path)
        LOG.debug("Set path for Housekeeper sample sheet in flow cell")

        try:
            is_flow_cell_ready_for_postprocessing(
                flow_cell_output_directory=flow_cell_out_directory,
                flow_cell=parsed_flow_cell,
                force=force,
            )
        except FlowCellError as e:
            LOG.error(f"Flow cell {flow_cell_directory_name} will be skipped: {e}")
            return

        try:
            self.store_flow_cell_data(parsed_flow_cell)
        except Exception as e:
            LOG.error(f"Failed to store flow cell data: {str(e)}")
            raise
        create_delivery_file_in_flow_cell_directory(flow_cell_out_directory)

    def finish_all_flow_cells(self) -> bool:
        """Finish all flow cells that need it."""
        flow_cell_dirs = self.get_all_demultiplexed_flow_cell_dirs()
        is_error_raised: bool = False
        for flow_cell_dir in flow_cell_dirs:
            try:
                self.finish_flow_cell(flow_cell_dir.name)
            except Exception as error:
                LOG.error(f"Failed to finish flow cell {flow_cell_dir.name}: {str(error)}")
                is_error_raised = True
                continue
        return is_error_raised

    def store_flow_cell_data(self, parsed_flow_cell: FlowCellDirectoryData) -> None:
        """Store data from the flow cell directory in status db and housekeeper."""
        store_flow_cell_data_in_status_db(
            parsed_flow_cell=parsed_flow_cell,
            store=self.status_db,
        )
        store_sequencing_metrics_in_status_db(flow_cell=parsed_flow_cell, store=self.status_db)
        update_sample_read_counts_in_status_db(
            flow_cell_data=parsed_flow_cell, store=self.status_db
        )
        store_flow_cell_data_in_housekeeper(
            flow_cell=parsed_flow_cell,
            hk_api=self.hk_api,
            flow_cell_run_dir=self.demux_api.flow_cells_dir,
            store=self.status_db,
        )

    def get_all_demultiplexed_flow_cell_dirs(self) -> List[Path]:
        """Return all demultiplex flow cell out directories."""
        demultiplex_flow_cells: List[Path] = []
        for flow_cell_dir in self.demux_api.demultiplexed_runs_dir.iterdir():
            if flow_cell_dir.is_dir():
                LOG.debug(f"Found directory {flow_cell_dir}")
                demultiplex_flow_cells.append(flow_cell_dir)
        return demultiplex_flow_cells
