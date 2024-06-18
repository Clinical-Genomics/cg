"""Tests for the read function pertaining to the Illumina Sequencing Run model."""

from datetime import datetime

from cg.store.models import IlluminaSequencingRun
from cg.store.store import Store


def test_get_latest_illumina_sequencing_run_for_case(
    re_sequenced_sample_illumina_data_store: Store,
    case_id_for_sample_on_multiple_flow_cells: str,
    flow_cells_with_the_same_sample: list[str],
    timestamp_yesterday: datetime,
):
    # GIVEN a store with a sample that has been sequenced twice
    first_run: IlluminaSequencingRun = (
        re_sequenced_sample_illumina_data_store.get_illumina_sequencing_run_by_device_internal_id(
            flow_cells_with_the_same_sample[0]
        )
    )
    first_run.sequencing_completed_at = timestamp_yesterday
    second_run: IlluminaSequencingRun = (
        re_sequenced_sample_illumina_data_store.get_illumina_sequencing_run_by_device_internal_id(
            flow_cells_with_the_same_sample[1]
        )
    )
    assert first_run
    assert second_run
    assert first_run.sequencing_completed_at < second_run.sequencing_completed_at

    # WHEN fetching the latest sequencing run for the sample
    latest_sequencing_run: IlluminaSequencingRun = (
        re_sequenced_sample_illumina_data_store.get_latest_illumina_sequencing_run_for_case(
            case_id_for_sample_on_multiple_flow_cells
        )
    )

    # THEN the latest sequencing run is returned
    assert latest_sequencing_run.device.internal_id == second_run.device.internal_id
