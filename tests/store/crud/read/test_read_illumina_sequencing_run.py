"""Tests for the read function pertaining to the Illumina Sequencing Run model."""

from datetime import datetime

import pytest

from cg.constants import SequencingRunDataAvailability, Workflow
from cg.exc import CgError
from cg.store.models import Case, IlluminaSequencingRun
from cg.store.store import Store


def test_get_latest_illumina_sequencing_run_for_nipt_case(
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
        re_sequenced_sample_illumina_data_store.get_latest_illumina_sequencing_run_for_nipt_case(
            case_id_for_sample_on_multiple_flow_cells
        )
    )

    # THEN the latest sequencing run is returned
    assert latest_sequencing_run.device.internal_id == second_run.device.internal_id


def test_get_latest_illumina_sequencing_run_for_nipt_case_fail(
    re_sequenced_sample_illumina_data_store: Store,
    case_id_for_sample_on_multiple_flow_cells: str,
    flow_cells_with_the_same_sample: list[str],
    timestamp_yesterday: datetime,
):
    # GIVEN a store with a sample that has been sequenced twice but is not a NIPT case
    case: Case = re_sequenced_sample_illumina_data_store.get_case_by_internal_id(
        case_id_for_sample_on_multiple_flow_cells
    )
    case.data_analysis = Workflow.MIP_DNA

    # WHEN fetching the latest sequencing run for the sample

    # THEN an error is raised
    with pytest.raises(CgError):
        re_sequenced_sample_illumina_data_store.get_latest_illumina_sequencing_run_for_nipt_case(
            case_id_for_sample_on_multiple_flow_cells
        )


def test_get_illumina_sequencing_run_by_data_availability(
    store_with_illumina_sequencing_data: Store,
):
    # GIVEN a store with Illumina Sequencing Runs with data availability

    # WHEN filtering sequencing runs by data availability
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_data_availability(
            [SequencingRunDataAvailability.ON_DISK]
        )
    )

    # THEN the runs with the availability are returned
    for sequencing_run in sequencing_runs:
        assert sequencing_run.data_availability == SequencingRunDataAvailability.ON_DISK


def test_get_illumina_sequencing_run_by_data_availability_non_existetnt_status(
    store_with_illumina_sequencing_data: Store,
):
    # GIVEN a store with Illumina Sequencing Runs with data availability

    # WHEN filtering sequencing runs by data availability
    sequencing_runs: list[IlluminaSequencingRun] = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_data_availability(
            ["non_existent_status"]
        )
    )

    # THEN no runs are returned
    assert not sequencing_runs
