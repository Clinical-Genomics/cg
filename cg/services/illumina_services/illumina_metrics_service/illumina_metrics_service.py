from datetime import datetime
from pathlib import Path

from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import UNDETERMINED
from cg.constants.devices import DeviceType
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina_services.illumina_metrics_service.bcl_convert_metrics_parser import (
    BCLConvertMetricsParser,
)
from cg.services.illumina_services.illumina_metrics_service.illumina_demux_version_service import (
    IlluminaDemuxVersionService,
)
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSequencingRunDTO,
    IlluminaSampleSequencingMetricsDTO,
)
from cg.store.models import (
    SampleLaneSequencingMetrics,
)
from cg.utils.flow_cell import get_flow_cell_id


class IlluminaMetricsService:
    """Service to generate database models related to Illumina flow cell metrics."""

    def create_sample_lane_sequencing_metrics_for_flow_cell(
        self,
        flow_cell_directory: Path,
    ) -> list[SampleLaneSequencingMetrics]:
        """Parse the demultiplexing metrics data into the sequencing statistics model."""
        metrics_parser = BCLConvertMetricsParser(flow_cell_directory)
        sample_internal_ids: list[str] = metrics_parser.get_sample_internal_ids()
        sample_lane_sequencing_metrics: list[SampleLaneSequencingMetrics] = []

        for sample_internal_id in sample_internal_ids:
            for lane in metrics_parser.get_lanes_for_sample(sample_internal_id=sample_internal_id):
                metrics: SampleLaneSequencingMetrics = self._create_bcl_convert_sequencing_metrics(
                    sample_internal_id=sample_internal_id, lane=lane, metrics_parser=metrics_parser
                )
                sample_lane_sequencing_metrics.append(metrics)
        return sample_lane_sequencing_metrics

    def create_undetermined_non_pooled_metrics(
        self,
        flow_cell: IlluminaRunDirectoryData,
    ) -> list[SampleLaneSequencingMetrics]:
        """Return sequencing metrics for any undetermined reads in non-pooled lanes."""

        non_pooled_lanes_and_samples: list[tuple[int, str]] = (
            flow_cell.sample_sheet.get_non_pooled_lanes_and_samples()
        )
        metrics_parser = BCLConvertMetricsParser(flow_cell.path)
        undetermined_metrics: list[SampleLaneSequencingMetrics] = []

        for lane, sample_internal_id in non_pooled_lanes_and_samples:
            if not metrics_parser.has_undetermined_reads_in_lane(lane):
                continue

            # Passing Undetermined as the sample id is required to extract the undetermined reads data.
            # BclConvert tags undetermined reads in a lane with the sample id "Undetermined".
            metrics: SampleLaneSequencingMetrics = self._create_bcl_convert_sequencing_metrics(
                sample_internal_id=UNDETERMINED, lane=lane, metrics_parser=metrics_parser
            )
            metrics.sample_internal_id = sample_internal_id
            undetermined_metrics.append(metrics)
        return undetermined_metrics

    @staticmethod
    def _create_bcl_convert_sequencing_metrics(
        sample_internal_id: str, lane: int, metrics_parser: BCLConvertMetricsParser
    ) -> SampleLaneSequencingMetrics:
        """Create sequencing metrics for a sample in a lane."""
        flow_cell_id: str = get_flow_cell_id(metrics_parser.bcl_convert_demultiplex_dir.name)

        total_reads: int = metrics_parser.calculate_total_reads_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        q30_bases_percent: float = metrics_parser.get_q30_bases_percent_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        mean_quality_score: float = metrics_parser.get_mean_quality_score_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        return SampleLaneSequencingMetrics(
            sample_internal_id=sample_internal_id,
            flow_cell_name=flow_cell_id,
            flow_cell_lane_number=lane,
            sample_total_reads_in_lane=total_reads,
            sample_base_percentage_passing_q30=q30_bases_percent,
            sample_base_mean_quality_score=mean_quality_score,
            created_at=datetime.now(),
        )

    @staticmethod
    def create_sample_run_metrics_dto(
        sample_internal_id: str,
        lane: int,
        metrics_parser: BCLConvertMetricsParser,
    ) -> IlluminaSampleSequencingMetricsDTO:
        """Create sequencing metrics for all lanes in a flow cell."""
        total_reads: int = metrics_parser.calculate_total_reads_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        q30_bases_percent: float = metrics_parser.get_q30_bases_percent_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        mean_quality_score: float = metrics_parser.get_mean_quality_score_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        yield_: float = metrics_parser.get_yield_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        yield_q30: float = metrics_parser.get_yield_q30_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )

        return IlluminaSampleSequencingMetricsDTO(
            sample_id=sample_internal_id,
            type=DeviceType.ILLUMINA,
            flow_cell_lane=lane,
            total_reads_in_lane=total_reads,
            base_passing_q30_percent=q30_bases_percent,
            base_mean_quality_score=mean_quality_score,
            yield_=yield_,
            yield_q30=yield_q30,
            created_at=datetime.now(),
        )

    def create_sample_run_dto_for_undetermined_reads(
        self,
        flow_cell: IlluminaRunDirectoryData,
    ) -> list[IlluminaSampleSequencingMetricsDTO]:
        """Return sequencing metrics for any undetermined reads in non-pooled lanes."""
        non_pooled_lanes_and_samples: list[tuple[int, str]] = (
            flow_cell.sample_sheet.get_non_pooled_lanes_and_samples()
        )
        metrics_parser = BCLConvertMetricsParser(flow_cell.path)
        undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO] = []

        for lane, sample_internal_id in non_pooled_lanes_and_samples:
            if not metrics_parser.has_undetermined_reads_in_lane(lane):
                continue

            # Passing Undetermined as the sample id is required to extract the undetermined reads data.
            # BclConvert tags undetermined reads in a lane with the sample id "Undetermined".
            metrics: IlluminaSampleSequencingMetricsDTO = self.create_sample_run_metrics_dto(
                sample_internal_id=UNDETERMINED, lane=lane, metrics_parser=metrics_parser
            )
            metrics.sample_id = sample_internal_id
            undetermined_metrics.append(metrics)
        return undetermined_metrics

    def create_sample_sequencing_metrics_dto_for_flow_cell(
        self,
        flow_cell_directory: Path,
    ) -> list[IlluminaSampleSequencingMetricsDTO]:
        """Parse the demultiplexing metrics data into the sequencing statistics model."""
        metrics_parser = BCLConvertMetricsParser(flow_cell_directory)
        sample_internal_ids: list[str] = metrics_parser.get_sample_internal_ids()
        sample_lane_sequencing_metrics: list[IlluminaSampleSequencingMetricsDTO] = []

        for sample_internal_id in sample_internal_ids:
            for lane in metrics_parser.get_lanes_for_sample(sample_internal_id=sample_internal_id):
                metrics: IlluminaSampleSequencingMetricsDTO = self.create_sample_run_metrics_dto(
                    sample_internal_id=sample_internal_id,
                    lane=lane,
                    metrics_parser=metrics_parser,
                )
                sample_lane_sequencing_metrics.append(metrics)
        return sample_lane_sequencing_metrics

    @staticmethod
    def create_illumina_sequencing_dto(
        demultiplexed_run_dir: IlluminaRunDirectoryData,
    ) -> IlluminaSequencingRunDTO:
        metrics_parser = BCLConvertMetricsParser(demultiplexed_run_dir.path)
        total_reads: int = metrics_parser.get_total_reads_for_flow_cell()
        total_undetermined_reads: int = metrics_parser.get_undetermined_reads_for_flow_cell()
        percent_undetermined_reads: float = (
            metrics_parser.get_percent_undetermined_reads_for_flow_cell()
        )
        percent_q30: float = metrics_parser.get_mean_percent_q30_for_flow_cell()
        mean_quality_score: float = metrics_parser.get_mean_quality_score_sum_for_flow_cell()
        total_yield: int = metrics_parser.get_yield_for_flow_cell()
        yield_q30: int = metrics_parser.get_yield_q30_for_flow_cell()
        cycles: int = demultiplexed_run_dir.run_parameters.get_read_1_cycles()
        software_service = IlluminaDemuxVersionService()
        demux_software: str = software_service.get_demux_software(
            demultiplexed_run_dir.demultiplex_software_info_path
        )
        demux_software_version: str = software_service.get_demux_software_version(
            demultiplexed_run_dir.demultiplex_software_info_path
        )
        sequencing_started_at: datetime = demultiplexed_run_dir.sequencing_started_at
        sequencing_comleted_at: datetime = demultiplexed_run_dir.sequencing_completed_at
        demultiplexing_started_at: datetime = demultiplexed_run_dir.demultiplexing_started_at
        demultiplexing_completed_at: datetime = demultiplexed_run_dir.demultiplexing_completed_at
        sequencer_type: str = demultiplexed_run_dir.sequencer_type
        sequencer_name: str = demultiplexed_run_dir.machine_name

        return IlluminaSequencingRunDTO(
            sequencer_type=sequencer_type,
            sequencer_name=sequencer_name,
            data_availability=FlowCellStatus.ON_DISK,
            archived_at=None,
            has_backup=False,
            total_reads=total_reads,
            total_undetermined_reads=total_undetermined_reads,
            percent_undetermined_reads=percent_undetermined_reads,
            percent_q30=percent_q30,
            mean_quality_score=mean_quality_score,
            total_yield=total_yield,
            yield_q30=yield_q30,
            cycles=cycles,
            demultiplexing_software=demux_software,
            demultiplexing_software_version=demux_software_version,
            sequencing_started_at=sequencing_started_at,
            sequencing_completed_at=sequencing_comleted_at,
            demultiplexing_started_at=demultiplexing_started_at,
            demultiplexing_completed_at=demultiplexing_completed_at,
            type=DeviceType.ILLUMINA,
        )
