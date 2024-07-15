"""Module for the illumina post-processing service factory."""

from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.sequencing import Sequencers
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.data_transfer.data_transfer_service import IlluminaDataTransferService
from cg.services.illumina.file_parsing.bcl_convert_metrics_parser import BCLConvertMetricsParser
from cg.services.illumina.file_parsing.demux_version_service import IlluminaDemuxVersionService
from cg.services.illumina.file_parsing.sequencing_times.collect_sequencing_times import (
    CollectSequencingTimes,
)
from cg.services.illumina.file_parsing.sequencing_times.hiseq_sequencers_sequencing_times_service import (
    HiseqSequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.novaseq_6000_sequencing_times_service import (
    Novaseq6000SequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.novaseq_x_sequencing_times_service import (
    NovaseqXSequencingTimesService,
)
from cg.services.illumina.file_parsing.sequencing_times.sequencing_times_service import (
    SequencingTimesService,
)
from cg.services.illumina.post_processing.post_processing_service import (
    IlluminaPostProcessingService,
)
from cg.store.store import Store


class PostProcessServiceFactory:

    def __init__(self, run_dir: Path, status_db: Store, hk_api: HousekeeperAPI, dry_run: bool):
        self.run_dir: Path = run_dir
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = hk_api
        self.dry_run: bool = dry_run

    def _create_run_directory_data(self) -> IlluminaRunDirectoryData:
        return IlluminaRunDirectoryData(self.run_dir)

    def _create_metrics_service(
        self,
    ) -> BCLConvertMetricsParser:
        return BCLConvertMetricsParser(self.run_dir)

    @staticmethod
    def _create_collect_sequencing_time_service(
        run_directory_data: IlluminaRunDirectoryData,
    ) -> CollectSequencingTimes:
        sequencing_time_service = get_sequencer_time_service(run_directory_data)
        return CollectSequencingTimes(sequencing_time_service)

    @staticmethod
    def _create_software_service(self) -> IlluminaDemuxVersionService:
        return IlluminaDemuxVersionService()

    def _create_transfer_service(self) -> IlluminaDataTransferService:
        metrics_parser: BCLConvertMetricsParser = self.create_metrics_service()
        sequencing_time_collector: CollectSequencingTimes = (
            self.create_collect_sequencing_time_service(self.create_run_directory_data())
        )
        software_service: IlluminaDemuxVersionService = self.create_software_service()
        return IlluminaDataTransferService(
            metrics_parser=metrics_parser,
            sequencing_time_collector=sequencing_time_collector,
            software_service=software_service,
        )

    def create_post_processing_service(self) -> IlluminaPostProcessingService:
        transfer_service: IlluminaDataTransferService = self.create_transfer_service()
        return IlluminaPostProcessingService(
            status_db=self.status_db,
            housekeeper_api=self.hk_api,
            demultiplexed_runs_dir=self.run_dir,
            transfer_service=transfer_service,
            dry_run=self.dry_run,
        )


sequencer_times_services: dict = {
    Sequencers.NOVASEQX: NovaseqXSequencingTimesService,
    Sequencers.NOVASEQ: Novaseq6000SequencingTimesService,
    Sequencers.HISEQX: HiseqSequencingTimesService,
    Sequencers.HISEQGA: HiseqSequencingTimesService,
}


def get_sequencer_time_service(run_directory_data) -> SequencingTimesService:
    return sequencer_times_services[run_directory_data.sequencer_type]
