from datetime import datetime
from pathlib import Path

from cg.apps.sequencing_metrics_parser.parser import MetricsParser
from cg.constants.demultiplexing import UNDETERMINED
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData
from cg.store.models import SampleLaneSequencingMetrics
from cg.utils.flow_cell import get_flow_cell_id


def create_sample_lane_sequencing_metrics_for_flow_cell(
    flow_cell_directory: Path,
) -> list[SampleLaneSequencingMetrics]:
    """Parse the demultiplexing metrics data into the sequencing statistics model."""
    metrics_parser = MetricsParser(flow_cell_directory)
    sample_internal_ids: list[str] = metrics_parser.get_sample_internal_ids()
    sample_lane_sequencing_metrics: list[SampleLaneSequencingMetrics] = []

    for sample_internal_id in sample_internal_ids:
        for lane in metrics_parser.get_lanes_for_sample(sample_internal_id=sample_internal_id):
            metrics: SampleLaneSequencingMetrics = _create_bcl_convert_sequencing_metrics(
                sample_internal_id=sample_internal_id, lane=lane, metrics_parser=metrics_parser
            )
            sample_lane_sequencing_metrics.append(metrics)
    return sample_lane_sequencing_metrics


def create_undetermined_non_pooled_metrics(
    flow_cell: FlowCellDirectoryData,
) -> list[SampleLaneSequencingMetrics]:
    """Return sequencing metrics for any undetermined reads in non-pooled lanes."""

    non_pooled_lanes_and_samples: list[tuple[int, str]] = (
        flow_cell.sample_sheet.get_non_pooled_lanes_and_samples()
    )
    metrics_parser = MetricsParser(flow_cell.path)
    undetermined_metrics: list[SampleLaneSequencingMetrics] = []

    for lane, sample_internal_id in non_pooled_lanes_and_samples:
        if not metrics_parser.has_undetermined_reads_in_lane(lane):
            continue

        # Passing Undetermined as the sample id is required to extract the undetermined reads data.
        # BclConvert tags undetermined reads in a lane with the sample id "Undetermined".
        metrics: SampleLaneSequencingMetrics = _create_bcl_convert_sequencing_metrics(
            sample_internal_id=UNDETERMINED, lane=lane, metrics_parser=metrics_parser
        )
        metrics.sample_internal_id = sample_internal_id
        undetermined_metrics.append(metrics)
    return undetermined_metrics


def _create_bcl_convert_sequencing_metrics(
    sample_internal_id: str, lane: int, metrics_parser: MetricsParser
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
