"""Tests for the status_db_storage_functions module of the demultiplexing post post-processing module."""

from mock import MagicMock

from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.meta.demultiplex.status_db_storage_functions import (
    add_sequencing_metrics_to_statusdb,
    delete_sequencing_metrics_from_statusdb,
    metric_has_sample_in_statusdb,
    update_sample_read_count,
)
from cg.models.cg_config import CGConfig
from cg.store.models import Flowcell, Sample, SampleLaneSequencingMetrics
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_add_single_sequencing_metrics_entry_to_statusdb(
    store_with_sequencing_metrics: Store,
    demultiplex_context: CGConfig,
    flow_cell_name: str,
    sample_id: str,
    lane: int = 1,
):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sequencing metrics entry
    sequencing_metrics_entry = store_with_sequencing_metrics.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=flow_cell_name, sample_internal_id=sample_id, lane=lane
    )

    # WHEN adding the sequencing metrics entry to the statusdb
    add_sequencing_metrics_to_statusdb(
        sample_lane_sequencing_metrics=[sequencing_metrics_entry],
        store=demux_post_processing_api.status_db,
    )

    # THEN the sequencing metrics entry was added to the statusdb
    assert demux_post_processing_api.status_db.get_metrics_entry_by_flow_cell_name_sample_internal_id_and_lane(
        flow_cell_name=flow_cell_name, sample_internal_id=sample_id, lane=lane
    )


def test_update_sample_read_count():
    # GIVEN a sample and a read count
    sample = Sample()
    read_count: int = 100

    # GIVEN a mocked status_db
    status_db = MagicMock()
    status_db.get_number_of_reads_for_sample_passing_q30_threshold.return_value = read_count

    # WHEN updating the sample read count
    update_sample_read_count(
        sample=sample,
        q30_threshold=0,
        store=status_db,
    )

    # THEN the reads have been updated with the read count for the sample
    assert sample.reads == read_count


def test_metric_has_sample_in_statusdb(demultiplex_context: CGConfig):
    # GIVEN a store with a sample and a sequencing metric

    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sample internal id that does not exist in statusdb
    sample_internal_id = "does_not_exist"

    # WHEN checking if the sample exists in statusdb
    assert not metric_has_sample_in_statusdb(
        sample_internal_id=sample_internal_id, store=demux_post_processing_api.status_db
    )


def test_delete_sequencing_metrics_from_statusdb_existing_metrics(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    # GIVEN a store with sequencing metrics
    store = store_with_sequencing_metrics

    # GIVEN that the flow cell has sequencing metrics
    metrics: list[SampleLaneSequencingMetrics] = (
        store.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell_name)
    )
    assert metrics

    # WHEN deleting sequencing metrics from statusdb
    delete_sequencing_metrics_from_statusdb(flow_cell_id=flow_cell_name, store=store)

    # THEN the sequencing metrics should be deleted from statusdb
    assert not store.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )


def test_delete_sequencing_metrics_from_statusdb_no_metrics(
    store_with_sequencing_metrics: Store,
    helpers: StoreHelpers,
):
    # GIVEN a store with sequencing metrics
    store = store_with_sequencing_metrics

    # GIVEN a new flow cell with no sequencing metrics
    flow_cell: Flowcell = helpers.add_flow_cell(store=store)
    metrics: list[SampleLaneSequencingMetrics] = (
        store.get_sample_lane_sequencing_metrics_by_flow_cell_name(flow_cell.name)
    )
    assert not metrics

    # WHEN deleting sequencing metrics from statusdb
    delete_sequencing_metrics_from_statusdb(flow_cell_id=flow_cell.name, store=store)

    # THEN no errors should be raised

    # THEN the sequencing metrics are still not in statusdb
    assert not store.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell.name
    )
