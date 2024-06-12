"""Module that holds the illumina post-processing service."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.devices import DeviceType
from cg.exc import MissingFilesError, FlowCellError
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_metrics_service.illumina_metrics_service import (
    IlluminaMetricsService,
)
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaFlowCellDTO,
    IlluminaSequencingRunDTO,
    IlluminaSampleSequencingMetricsDTO,
)
from cg.services.illumina_services.illumina_post_processing_service.utils import (
    create_delivery_file_in_flow_cell_directory,
    combine_sample_metrics_with_undetermined,
)
from cg.services.illumina_services.illumina_post_processing_service.validation import (
    is_flow_cell_ready_for_postprocessing,
)
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class IlluminaPostProcessingService:
    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI, dry_run: bool) -> None:
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.dry_run: bool = dry_run

    def store_illumina_flow_cell(
        self,
        flow_cell_dir_data: IlluminaRunDirectoryData,
    ) -> IlluminaFlowCell:
        """
        Create Illumina flow cell from the parsed and validated flow cell directory data.
        And add the samples on the flow cell to the model.
        """
        model: str | None = flow_cell_dir_data.run_parameters.get_flow_cell_model()
        flow_cell_dto = IlluminaFlowCellDTO(
            internal_id=flow_cell_dir_data.id, type=DeviceType.ILLUMINA, model=model
        )
        return self.status_db.add_illumina_flow_cell(flow_cell_dto)

    def store_illumina_sequencing_run(
        self,
        flow_cell_dir_data: IlluminaRunDirectoryData,
        flow_cell: IlluminaFlowCell,
    ) -> IlluminaSequencingRun:
        """Store illumina run metrics in the status database."""
        metrics_service = IlluminaMetricsService()
        sequencing_run_dto: IlluminaSequencingRunDTO = (
            metrics_service.create_illumina_sequencing_dto(flow_cell_dir_data)
        )
        return self.status_db.add_illumina_sequencing_run(
            sequencing_run_dto=sequencing_run_dto, flow_cell=flow_cell
        )

    def store_illumina_sample_sequencing_metrics(
        self,
        flow_cell_dir_data: IlluminaRunDirectoryData,
        sequencing_run: IlluminaSequencingRun,
    ):
        """Store illumina sample sequencing metrics in the status database."""
        metrics_service = IlluminaMetricsService()
        sample_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            metrics_service.create_sample_sequencing_metrics_dto_for_flow_cell(
                flow_cell_directory=flow_cell_dir_data.path,
            )
        )
        undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            metrics_service.create_sample_run_dto_for_undetermined_reads(flow_cell_dir_data)
        )

        combined_metrics = combine_sample_metrics_with_undetermined(
            sample_metrics=sample_metrics,
            undetermined_metrics=undetermined_metrics,
        )
        return self.status_db.add_illumina_sample_metrics(
            sample_metrics_dto=combined_metrics, sequencing_run=sequencing_run
        )

    def store_illumina_flow_cell_data(self, flow_cell_dir_data: IlluminaRunDirectoryData) -> None:
        """Store flow cell data in the status database."""
        flow_cell: IlluminaFlowCell = self.store_illumina_flow_cell(
            flow_cell_dir_data=flow_cell_dir_data
        )
        sequencing_run: IlluminaSequencingRun = self.store_illumina_sequencing_run(
            flow_cell_dir_data=flow_cell_dir_data, flow_cell=flow_cell
        )
        self.store_illumina_sample_sequencing_metrics(
            flow_cell_dir_data=flow_cell_dir_data, sequencing_run=sequencing_run
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
        flow_cell = IlluminaRunDirectoryData(flow_cell_out_directory)
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
