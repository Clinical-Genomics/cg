from datetime import datetime
from pathlib import Path

from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import UNDETERMINED
from cg.constants.devices import DeviceType
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.services.illumina_services.illumina_metrics_service.bcl_convert_metrics_parser import (
    BCLConvertMetricsParser,
)
from cg.services.illumina_services.illumina_metrics_service.illumina_demux_version_service import (
    IlluminaDemuxVersionService,
)
from cg.store.models import (
    SampleLaneSequencingMetrics,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    IlluminaFlowCell,
)
from cg.store.store import Store
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
        flow_cell: FlowCellDirectoryData,
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
    def create_sample_run_metrics(
        sample_internal_id: str,
        lane: int,
        metrics_parser: BCLConvertMetricsParser,
        store: Store,
    ) -> IlluminaSampleSequencingMetrics:
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
        sample_id: int = store.get_sample_by_internal_id(sample_internal_id).id

        yield_: float = metrics_parser.get_yield_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )
        yield_q30: float = metrics_parser.get_yield_q30_for_sample_in_lane(
            sample_internal_id=sample_internal_id, lane=lane
        )

        return IlluminaSampleSequencingMetrics(
            sample_id=sample_id,
            instrument_run_id=instrument_run_id,
            type=DeviceType.ILLUMINA,
            flow_cell_lane=lane,
            total_reads_in_lane=total_reads,
            base_percentage_passing_q30=q30_bases_percent,
            base_mean_quality_score=mean_quality_score,
            yield_=yield_,
            yield_q30=yield_q30,
            created_at=datetime.now(),
        )

    def create_sample_sequencing_metrics_for_flow_cell(
        self,
        flow_cell_directory: Path,
        store: Store,
    ) -> list[IlluminaSampleSequencingMetrics]:
        """Parse the demultiplexing metrics data into the sequencing statistics model."""
        metrics_parser = BCLConvertMetricsParser(flow_cell_directory)
        sample_internal_ids: list[str] = metrics_parser.get_sample_internal_ids()
        sample_lane_sequencing_metrics: list[IlluminaSampleSequencingMetrics] = []

        for sample_internal_id in sample_internal_ids:
            for lane in metrics_parser.get_lanes_for_sample(sample_internal_id=sample_internal_id):
                metrics: IlluminaSampleSequencingMetrics = self.create_sample_run_metrics(
                    sample_internal_id=sample_internal_id,
                    lane=lane,
                    metrics_parser=metrics_parser,
                    store=store,
                )
                sample_lane_sequencing_metrics.append(metrics)
        return sample_lane_sequencing_metrics

    @staticmethod
    def create_illumina_sequencing_run(
        flow_cell_dir_data: FlowCellDirectoryData,
    ) -> IlluminaSequencingRun:
        metrics_parser = BCLConvertMetricsParser(flow_cell_dir_data.path)
        total_reads: int = metrics_parser.get_total_reads_for_flow_cell()
        total_undetermined_reads: int = metrics_parser.get_undetermined_reads_for_flow_cell()
        percent_undetermined_reads: float = (
            metrics_parser.get_percent_undetermined_reads_for_flow_cell()
        )
        percent_q30: float = metrics_parser.get_mean_percent_q30_for_flow_cell()
        mean_quality_score: float = metrics_parser.get_mean_quality_score_sum_for_flow_cell()
        total_yield: int = metrics_parser.get_yield_for_flow_cell()
        yield_q30: int = metrics_parser.get_yield_q30_for_flow_cell()
        cycles: int = flow_cell_dir_data.run_parameters.get_read_1_cycles()
        software_service = IlluminaDemuxVersionService()
        demux_software: str = software_service.get_demux_software(
            flow_cell_dir_data.demultiplex_software_info_path
        )
        demux_software_version: str = software_service.get_demux_software_version(
            flow_cell_dir_data.demultiplex_software_info_path
        )
        sequencing_started_at: datetime = flow_cell_dir_data.sequencing_started_at
        sequencing_comleted_at: datetime = flow_cell_dir_data.sequencing_completed_at
        demultiplexing_started_at: datetime = flow_cell_dir_data.demultiplexing_started_at
        demultiplexing_completed_at: datetime = flow_cell_dir_data.demultiplexing_completed_at
        sequencer_type: str = flow_cell_dir_data.sequencer_type
        sequencer_name: str = flow_cell_dir_data.machine_name

        return IlluminaSequencingRun(
            sequencer_type=sequencer_type,
            sequencer_name=sequencer_name,
            data_availablilty=FlowCellStatus.ON_DISK,
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
            demux_software=demux_software,
            demux_software_version=demux_software_version,
            sequencing_started_at=sequencing_started_at,
            sequencing_comleted_at=sequencing_comleted_at,
            demultiplexing_started_at=demultiplexing_started_at,
            demultiplexing_completed_at=demultiplexing_completed_at,
        )
