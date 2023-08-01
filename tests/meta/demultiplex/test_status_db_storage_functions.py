"""Tests for the status_db_storage_functions module of the demultiplexing post post-processing module."""
from mock import MagicMock

from cg.meta.demultiplex.demux_post_processing import (
    DemuxPostProcessingAPI,
)

from cg.models.cg_config import CGConfig

from cg.store import Store

from cg.meta.demultiplex.status_db_storage_functions import (
    add_sequencing_metrics_to_statusdb,
    update_sample_read_count,
    metric_has_sample_in_statusdb,
)


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


def test_update_sample_read_count(demultiplex_context: CGConfig):
    # GIVEN a DemuxPostProcessing API
    demux_post_processing_api = DemuxPostProcessingAPI(demultiplex_context)

    # GIVEN a sample id and a q30 threshold
    sample_internal_id = "sample_1"
    q30_threshold = 0

    # GIVEN a sample and a read count
    sample = MagicMock()
    read_count = 100

    # GIVEN a mocked status_db
    status_db = MagicMock()
    status_db.get_sample_by_internal_id.return_value = sample
    status_db.get_number_of_reads_for_sample_passing_q30_threshold.return_value = read_count
    demux_post_processing_api.status_db = status_db

    # WHEN calling update_sample_read_count
    update_sample_read_count(
        sample_id=sample_internal_id, q30_threshold=q30_threshold, store=status_db
    )

    # THEN get_sample_by_internal_id is called with the correct argument
    status_db.get_sample_by_internal_id.assert_called_with(sample_internal_id)

    # THEN get_number_of_reads_for_sample_passing_q30_threshold is called with the correct arguments
    status_db.get_number_of_reads_for_sample_passing_q30_threshold.assert_called_with(
        sample_internal_id=sample_internal_id,
        q30_threshold=q30_threshold,
    )

    # THEN the calculated_read_count has been updated with the read count for the sample
    assert sample.calculated_read_count == read_count


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
