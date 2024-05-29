"""Module that holds the illumina post-processing service."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.devices import DeviceType
from cg.exc import MissingFilesError, FlowCellError
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.services.illumina_services.illumina_metrics_service.illumina_metrics_service import (
    IlluminaMetricsService,
)
from cg.services.illumina_services.illumina_post_processing_service.utils import (
    create_delivery_file_in_flow_cell_directory,
)
from cg.services.illumina_services.illumina_post_processing_service.validation import (
    is_flow_cell_ready_for_postprocessing,
)
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun, IlluminaSampleSequencingMetrics
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class IlluminaPostProcessingService:
    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI, dry_run: bool) -> None:
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.dry_run: bool = False

    @staticmethod
    def get_illumina_flow_cell(
        flow_cell_dir_data: FlowCellDirectoryData,
    ) -> IlluminaFlowCell:
        """
        Create Illumina flow cell from the parsed and validated flow cell directory data.
        And add the samples on the flow cell to the model.
        """
        model: str | None = flow_cell_dir_data.run_parameters.get_flow_cell_model()
        new_flow_cell = IlluminaFlowCell(
            internal_id=flow_cell_dir_data.id, type=DeviceType.ILLUMINA, model=model
        )
        return new_flow_cell

    @staticmethod
    def get_illumina_sequencing_run(
        flow_cell_dir_data: FlowCellDirectoryData,
    ) -> IlluminaSequencingRun:
        """Store illumina run metrics in the status database."""
        metrics_service = IlluminaMetricsService()
        return metrics_service.create_illumina_sequencing_run(flow_cell_dir_data)

    def get_illumina_sample_sequencing_metrics(
        self,
        flow_cell_dir_data: FlowCellDirectoryData,
    ) -> list[IlluminaSampleSequencingMetrics]:
        """Store illumina sample sequencing metrics in the status database."""
        metrics_service = IlluminaMetricsService()
        return metrics_service.create_sample_sequencing_metrics_for_flow_cell(
            flow_cell_directory=flow_cell_dir_data.path, store=self.status_db
        )

    @staticmethod
    def relate_illumina_models(
        flow_cell: IlluminaFlowCell,
        sequencing_run: IlluminaSequencingRun,
        sample_metrics: list[IlluminaSampleSequencingMetrics],
    ) -> tuple[IlluminaFlowCell, IlluminaSequencingRun, list[IlluminaSampleSequencingMetrics]]:
        sequencing_run.device = flow_cell
        sequencing_run.sample_metrics = sample_metrics
        return flow_cell, sequencing_run, sample_metrics

    @staticmethod
    def add_illumina_models_to_store(
        flow_cell: IlluminaFlowCell,
        sequencing_run: IlluminaSequencingRun,
        sample_metrics: list[IlluminaSampleSequencingMetrics],
        store: Store,
    ) -> None:
        store.add_illumina_flow_cell(flow_cell)
        store.add_illumina_sequencing_run(sequencing_run)
        store.add_illumina_sample_metrics(sample_metrics)

    def store_illumina_flow_cell_data(self, flow_cell_dir_data: FlowCellDirectoryData) -> None:
        """Store flow cell data in the status database."""
        flow_cell: IlluminaFlowCell = self.get_illumina_flow_cell(
            flow_cell_dir_data=flow_cell_dir_data
        )
        sequencing_run: IlluminaSequencingRun = self.get_illumina_sequencing_run(flow_cell_dir_data)
        sample_metrics: list[IlluminaSampleSequencingMetrics] = (
            self.get_illumina_sample_sequencing_metrics(flow_cell_dir_data)
        )
        flow_cell, sequencing_run, sample_metrics = self.relate_illumina_models(
            flow_cell, sequencing_run, sample_metrics
        )
        self.add_illumina_models_to_store(
            flow_cell=flow_cell, sequencing_run=sequencing_run, sample_metrics=sample_metrics
        )
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
