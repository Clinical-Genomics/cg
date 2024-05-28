"""Module that holds the illumina post-processing service."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.devices import DeviceType
from cg.exc import MissingFilesError, FlowCellError
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.services.illumina_post_processing_service.utils import (
    create_delivery_file_in_flow_cell_directory,
)
from cg.services.illumina_post_processing_service.validation import (
    is_flow_cell_ready_for_postprocessing,
)
from cg.store.models import IlluminaFlowCell
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class IlluminaPostProcessingService:
    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI, dry_run: bool) -> None:
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.dry_run: bool = False

    @staticmethod
    def store_illumina_flow_cell(
        flow_cell: FlowCellDirectoryData,
        store: Store,
    ) -> IlluminaFlowCell:
        """
        Create flow cell from the parsed and validated flow cell data.
        And add the samples on the flow cell to the model.
        """
        model: str | None = flow_cell.run_parameters.get_flow_cell_model()
        new_flow_cell = IlluminaFlowCell(
            internal_id=flow_cell.id, type=DeviceType.ILLUMINA, model=model
        )
        return store.add_illumina_flow_cell(new_flow_cell)

    @staticmethod
    def store_illumina_sequencing_metrics(flow_cell: IlluminaFlowCell) -> None:
        """Store illumina run metrics in the status database."""
        pass

    @staticmethod
    def store_illumina_sample_sequencing_metrics():
        """Store illumina sample sequencing metrics in the status database."""
        pass

    def store_illumina_flow_cell_data(self, flow_cell: FlowCellDirectoryData) -> None:
        """Store flow cell data in the status database."""
        flow_cell: IlluminaFlowCell = self.store_illumina_flow_cell(
            flow_cell=flow_cell, store=self.status_db
        )
        self.store_illumina_sequencing_metrics(flow_cell)
        self.store_illumina_sample_sequencing_metrics()
        self.status_db.commit_to_store()

    def post_process_illumina_flow_cell(
        self,
        flow_cell_directory_name: str,
        demultiplexed_runs_dir: Path,
    ) -> None:
        """Store data for the demultiplexed flow cell and mark it as ready for delivery.
        This function:
            - Stores the flow cell in the status database
            - Stores sequencing metrics in the status database
            - Updates sample read counts in the status database
            - Stores the flow cell data in the housekeeper database
            - Creates a delivery file in the flow cell directory
        Raises:
            FlowCellError: If the flow cell directory or the data it contains is not valid.
        """

        LOG.info(f"Post-process flow cell {flow_cell_directory_name}")
        flow_cell_out_directory = Path(demultiplexed_runs_dir, flow_cell_directory_name)
        flow_cell = FlowCellDirectoryData(flow_cell_out_directory)
        sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(flow_cell.id)
        flow_cell.set_sample_sheet_path_hk(hk_path=sample_sheet_path)

        LOG.debug("Set path for Housekeeper sample sheet in flow cell")
        try:
            is_flow_cell_ready_for_postprocessing(
                flow_cell_output_directory=flow_cell_out_directory,
                flow_cell=flow_cell,
            )
        except (FlowCellError, MissingFilesError) as e:
            LOG.warning(f"Flow cell {flow_cell_directory_name} will be skipped: {e}")
            return
        if self.dry_run:
            LOG.info(f"Dry run will not finish flow cell {flow_cell_directory_name}")
            return
        try:
            self.store_illumina_flow_cell_data(flow_cell)
        except Exception as e:
            LOG.error(f"Failed to store flow cell data: {str(e)}")
            raise
        create_delivery_file_in_flow_cell_directory(flow_cell_out_directory)
