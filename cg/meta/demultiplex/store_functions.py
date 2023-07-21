"""Functions interacting with statusdb in the DemuxPostProcessingAPI."""
from typing import List, Optional
import logging

from cg.store.models import Sample

from cg.apps.sequencing_metrics_parser.api import (
    create_sample_lane_sequencing_metrics_for_flow_cell,
)

from cg.meta.demultiplex.utils import (
    get_q30_threshold,
)
from cg.apps.demultiplex.sample_sheet.read_sample_sheet import (
    get_sample_internal_ids_from_sample_sheet,
)

from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.store import Store
from cg.store.models import Flowcell, SampleLaneSequencingMetrics

LOG = logging.getLogger(__name__)


def store_flow_cell_data_in_status_db(
    parsed_flow_cell: FlowCellDirectoryData, store: Store
) -> None:
    """Create flow cell from the parsed and validated flow cell data."""
    if not store.get_flow_cell_by_name(flow_cell_name=parsed_flow_cell.id):
        flow_cell: Flowcell = Flowcell(
            name=parsed_flow_cell.id,
            sequencer_type=parsed_flow_cell.sequencer_type,
            sequencer_name=parsed_flow_cell.machine_name,
            sequenced_at=parsed_flow_cell.run_date,
        )
        store.session.add(flow_cell)
        store.session.commit()
        LOG.info(f"Flow cell added to status db: {parsed_flow_cell.id}.")
    else:
        LOG.info(f"Flow cell already exists in status db: {parsed_flow_cell.id}. Skipping.")


def store_sequencing_metrics_in_status_db(flow_cell: FlowCellDirectoryData, store: Store) -> None:
    sample_lane_sequencing_metrics: List[
        SampleLaneSequencingMetrics
    ] = create_sample_lane_sequencing_metrics_for_flow_cell(
        flow_cell_directory=flow_cell.path,
        bcl_converter=flow_cell.bcl_converter,
    )
    add_sequencing_metrics_to_statusdb(
        sample_lane_sequencing_metrics=sample_lane_sequencing_metrics, store=store
    )

    LOG.info(f"Added sequencing metrics to status db for: {flow_cell.id}")


def add_sequencing_metrics_to_statusdb(
    sample_lane_sequencing_metrics: List[SampleLaneSequencingMetrics], store: Store
) -> None:
    for metric in sample_lane_sequencing_metrics:
        metric_exists: bool = metric_exists_in_status_db(metric=metric, store=store)
        metric_has_sample: bool = metric_has_sample_in_statusdb(
            sample_internal_id=metric.sample_internal_id, store=store
        )
        if not metric_exists and metric_has_sample:
            LOG.debug(
                f"Adding sample lane sequencing metrics for {metric.flow_cell_name}, {metric.sample_internal_id}, and {metric.flow_cell_lane_number}."
            )
            store.session.add(metric)
    store.session.commit()


def metric_has_sample_in_statusdb(sample_internal_id: str, store: Store) -> bool:
    """Check if a sample exists in status db for the sample lane sequencing metrics."""
    sample: Sample = store.get_sample_by_internal_id(sample_internal_id)
    if sample:
        return True
    LOG.warning(f"Sample {sample_internal_id} does not exist in status db. Skipping.")
    return False


def metric_exists_in_status_db(metric: SampleLaneSequencingMetrics, store: Store) -> bool:
    existing_metrics_entry: Optional[
        SampleLaneSequencingMetrics
    ] = store.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=metric.flow_cell_name,
        sample_internal_id=metric.sample_internal_id,
        lane=metric.flow_cell_lane_number,
    )
    if existing_metrics_entry:
        LOG.warning(
            f"Sample lane sequencing metrics already exist for {metric.flow_cell_name}, {metric.sample_internal_id}, and lane {metric.flow_cell_lane_number}. Skipping."
        )
    return bool(existing_metrics_entry)


def update_sample_read_counts_in_status_db(
    flow_cell_data: FlowCellDirectoryData, store: Store
) -> None:
    """Update samples in status db with the sum of all read counts for the sample in the sequencing metrics table."""
    q30_threshold: int = get_q30_threshold(flow_cell_data.sequencer_type)
    sample_internal_ids: List[str] = get_sample_internal_ids_from_sample_sheet(
        sample_sheet_path=flow_cell_data.sample_sheet_path,
        flow_cell_sample_type=flow_cell_data.sample_type,
    )
    for sample_id in sample_internal_ids:
        update_sample_read_count(sample_id=sample_id, q30_threshold=q30_threshold, store=store)
    store.session.commit()


def update_sample_read_count(sample_id: str, q30_threshold: int, store: Store) -> None:
    """Update the read count for a sample in status db with all reads exceeding the q30 threshold from the sequencing metrics table."""
    sample: Optional[Sample] = store.get_sample_by_internal_id(sample_id)

    if sample:
        sample_read_count: int = store.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id,
            q30_threshold=q30_threshold,
        )
        LOG.debug(f"Updating sample {sample_id} with read count {sample_read_count}")
        sample.calculated_read_count = sample_read_count
    else:
        LOG.warning(f"Cannot find {sample_id} in status_db when adding read counts. Skipping.")
