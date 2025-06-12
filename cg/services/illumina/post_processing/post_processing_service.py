"""Module that holds the illumina post-processing service."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.devices import DeviceType
from cg.exc import FlowCellError, MissingFilesError
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.data_transfer.data_transfer_service import (
    IlluminaDataTransferService,
)
from cg.services.illumina.data_transfer.models import (
    IlluminaFlowCellDTO,
    IlluminaSampleSequencingMetricsDTO,
    IlluminaSequencingRunDTO,
)
from cg.services.illumina.post_processing.housekeeper_storage import (
    add_demux_logs_to_housekeeper,
    add_run_parameters_file_to_housekeeper,
    add_sample_fastq_files_to_housekeeper,
    delete_sequencing_data_from_housekeeper,
    store_undetermined_fastq_files,
)
from cg.services.illumina.post_processing.utils import (
    combine_sample_metrics_with_undetermined,
    create_delivery_file_in_flow_cell_directory,
)
from cg.services.illumina.post_processing.validation import (
    is_flow_cell_ready_for_postprocessing,
)
from cg.store.exc import EntryNotFoundError
from cg.store.models import IlluminaFlowCell, IlluminaSequencingRun
from cg.store.store import Store
from cg.utils.files import get_directories_in_path

LOG = logging.getLogger(__name__)


class IlluminaPostProcessingService:
    def __init__(
        self,
        status_db: Store,
        housekeeper_api: HousekeeperAPI,
        demultiplexed_runs_dir: Path,
        dry_run: bool,
    ) -> None:
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = housekeeper_api
        self.demultiplexed_runs_dir = demultiplexed_runs_dir
        self.dry_run: bool = dry_run

    def store_illumina_flow_cell(
        self,
        run_directory_data: IlluminaRunDirectoryData,
    ) -> IlluminaFlowCell:
        """
        Create Illumina flow cell from the parsed and validated run directory data
        and add the run samples to the model.
        """
        model: str | None = run_directory_data.run_parameters.get_flow_cell_model()
        flow_cell_dto = IlluminaFlowCellDTO(
            internal_id=run_directory_data.id, type=DeviceType.ILLUMINA, model=model
        )
        return self.status_db.add_illumina_flow_cell(flow_cell_dto)

    def store_illumina_sequencing_run(
        self,
        run_directory_data: IlluminaRunDirectoryData,
        flow_cell: IlluminaFlowCell,
    ) -> IlluminaSequencingRun:
        """Store Illumina run metrics in the status database."""
        metrics_service = IlluminaDataTransferService()
        sequencing_run_dto: IlluminaSequencingRunDTO = (
            metrics_service.create_illumina_sequencing_dto(run_directory_data)
        )
        return self.status_db.add_illumina_sequencing_run(
            sequencing_run_dto=sequencing_run_dto, flow_cell=flow_cell
        )

    def store_illumina_sample_sequencing_metrics(
        self,
        run_directory_data: IlluminaRunDirectoryData,
        sequencing_run: IlluminaSequencingRun,
    ) -> list[IlluminaSampleSequencingMetricsDTO]:
        """Store Illumina sample sequencing metrics in the status database."""
        metrics_service = IlluminaDataTransferService()
        sample_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            metrics_service.create_sample_sequencing_metrics_dto_for_flow_cell(
                flow_cell_directory=run_directory_data.get_demultiplexed_runs_dir(),
            )
        )
        undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            metrics_service.create_sample_run_dto_for_undetermined_reads(run_directory_data)
        )
        combined_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            combine_sample_metrics_with_undetermined(
                sample_metrics=sample_metrics,
                undetermined_metrics=undetermined_metrics,
            )
        )
        for sample_metric in combined_metrics:
            self.status_db.add_illumina_sample_metrics_entry(
                metrics_dto=sample_metric, sequencing_run=sequencing_run
            )
        return combined_metrics

    def store_sequencing_data_in_status_db(
        self, run_directory_data: IlluminaRunDirectoryData
    ) -> None:
        """Store all Illumina sequencing data in the status database."""
        LOG.info(f"Add sequencing and demux data to StatusDB for run {run_directory_data.id}")
        flow_cell: IlluminaFlowCell = self.store_illumina_flow_cell(
            run_directory_data=run_directory_data
        )
        sequencing_run: IlluminaSequencingRun = self.store_illumina_sequencing_run(
            run_directory_data=run_directory_data, flow_cell=flow_cell
        )
        sample_metrics: list[IlluminaSampleSequencingMetricsDTO] = (
            self.store_illumina_sample_sequencing_metrics(
                run_directory_data=run_directory_data, sequencing_run=sequencing_run
            )
        )
        self.update_samples_for_metrics(
            sample_metrics=sample_metrics, sequencing_run=sequencing_run
        )
        self.status_db.commit_to_store()

    def update_samples_for_metrics(
        self,
        sample_metrics: list[IlluminaSampleSequencingMetricsDTO],
        sequencing_run: IlluminaSequencingRun,
    ) -> None:
        unique_samples_on_run: list[str] = self.get_unique_samples_from_run(sample_metrics)
        for sample_id in unique_samples_on_run:
            self.status_db.update_sample_reads_illumina(
                internal_id=sample_id, sequencer_type=sequencing_run.sequencer_type
            )
            self.status_db.update_sample_sequenced_at(
                sample_id, date=sequencing_run.sequencing_completed_at
            )

    @staticmethod
    def get_unique_samples_from_run(
        sample_metrics: list[IlluminaSampleSequencingMetricsDTO],
    ) -> list[str]:
        """Get unique samples from the run."""
        return list({sample_metric.sample_id for sample_metric in sample_metrics})

    def store_sequencing_data_in_housekeeper(
        self,
        run_directory_data: IlluminaRunDirectoryData,
        store: Store,
    ) -> None:
        """Store fastq files, demux logs and run parameters for sequencing run in Housekeeper."""
        LOG.info(f"Add sequencing and demux data to Housekeeper for run {run_directory_data.id}")

        self.hk_api.add_bundle_and_version_if_non_existent(run_directory_data.id)
        tags: list[str] = [
            SequencingFileTag.FASTQ,
            SequencingFileTag.RUN_PARAMETERS,
            run_directory_data.id,
        ]
        self.hk_api.add_tags_if_non_existent(tags)
        add_sample_fastq_files_to_housekeeper(
            run_directory_data=run_directory_data, hk_api=self.hk_api, store=store
        )
        store_undetermined_fastq_files(
            run_directory_data=run_directory_data, hk_api=self.hk_api, store=store
        )
        add_demux_logs_to_housekeeper(
            run_directory_data=run_directory_data,
            hk_api=self.hk_api,
        )
        add_run_parameters_file_to_housekeeper(
            run_directory_data=run_directory_data,
            hk_api=self.hk_api,
        )

    def post_process_illumina_flow_cell(
        self,
        sequencing_run_name: str,
    ) -> None:
        """Store data for an Illumina demultiplexed run and mark it as ready for delivery.
        This function:
            - Stores the run data in the status database
            - Stores sequencing metrics in the status database
            - Updates sample read counts in the status database
            - Stores the run data in the Housekeeper database
            - Creates a delivery file in the sequencing run directory
        Raises:
            FlowCellError: If the flow cell directory or the data it contains is not valid.
        """

        LOG.info(f"Post-process Illumina run {sequencing_run_name}")
        demux_run_dir = Path(self.demultiplexed_runs_dir, sequencing_run_name)
        run_directory_data = IlluminaRunDirectoryData(demux_run_dir)
        sample_sheet_path: Path = self.hk_api.get_sample_sheet_path(run_directory_data.id)
        run_directory_data.set_sample_sheet_path_hk(hk_path=sample_sheet_path)
        sequencing_run: IlluminaSequencingRun | None = None
        has_backup: bool = False

        LOG.debug("Set path for Housekeeper sample sheet in run directory")
        try:
            is_flow_cell_ready_for_postprocessing(
                flow_cell_output_directory=demux_run_dir,
                flow_cell=run_directory_data,
            )
        except (FlowCellError, MissingFilesError) as e:
            LOG.warning(f"Run {sequencing_run_name} will be skipped: {e}")
            return
        if self.dry_run:
            LOG.info(f"Dry run: will not post-process Illumina run {sequencing_run_name}")
            return
        try:
            sequencing_run: IlluminaSequencingRun = (
                self.status_db.get_illumina_sequencing_run_by_device_internal_id(
                    run_directory_data.id
                )
            )
            has_backup: bool = sequencing_run.has_backup
        except EntryNotFoundError as error:
            LOG.info(f"Run {sequencing_run_name} not found in StatusDB: {str(error)}")
        self.delete_sequencing_run_data(flow_cell_id=run_directory_data.id)
        try:
            self.store_sequencing_data_in_status_db(run_directory_data)
            self.store_sequencing_data_in_housekeeper(
                run_directory_data=run_directory_data,
                store=self.status_db,
            )
        except Exception as e:
            LOG.error(f"Failed to store Illumina run: {str(e)}")
            self.status_db.rollback()
            raise
        if sequencing_run:
            self.status_db.update_illumina_sequencing_run_has_backup(
                sequencing_run=sequencing_run, has_backup=has_backup
            )

        create_delivery_file_in_flow_cell_directory(demux_run_dir)

    def get_all_demultiplexed_runs(self) -> list[Path]:
        """Get all demultiplexed Illumina runs."""
        return get_directories_in_path(self.demultiplexed_runs_dir)

    def post_process_all_runs(self) -> bool:
        """Post process all demultiplex illumina runs that need it."""
        demux_dirs = self.get_all_demultiplexed_runs()
        is_error_raised: bool = False
        for demux_dir in demux_dirs:
            try:
                self.post_process_illumina_flow_cell(demux_dir.name)
            except Exception as error:
                LOG.error(
                    f"Failed to post process demultiplexed Illumina run {demux_dir.name}: {str(error)}"
                )
                is_error_raised = True
                continue
        return is_error_raised

    def delete_sequencing_run_data(self, flow_cell_id: str):
        """Delete sequencing run entries from Housekeeper and StatusDB."""
        try:
            self.status_db.delete_illumina_flow_cell(flow_cell_id)
        except EntryNotFoundError:
            LOG.warning(f"Flow cell {flow_cell_id} not found in StatusDB.")
        delete_sequencing_data_from_housekeeper(flow_cell_id=flow_cell_id, hk_api=self.hk_api)
