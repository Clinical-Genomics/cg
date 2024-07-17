"""Tests for the sequencing times run services."""

from datetime import datetime

import pytest


@pytest.mark.parametrize(
    "run_dir_data, time_service, expected_time",
    [
        (
            "novaseq_x_flow_cell",
            "novaseq_x_sequencing_times_service",
            "novaseq_x_sequencing_start_time",
        ),
        (
            "novaseq_6000_pre_1_5_kits_flow_cell",
            "novaseq_6000_sequencing_times_service",
            "novaseq_6000_sequencing_start_time",
        ),
        (
            "hiseq_2500_dual_index_flow_cell",
            "hiseq_sequencing_times_service",
            "hiseq_sequencing_start_time",
        ),
    ],
)
def test_get_sequencing_start_time(run_dir_data, time_service, expected_time, request):
    # GIVEN run directory data and a time service
    run_dir_data = request.getfixturevalue(run_dir_data)
    time_service = request.getfixturevalue(time_service)
    expected_time = request.getfixturevalue(expected_time)

    # WHEN retrieving the start time
    start_time: datetime = time_service.get_start_time(run_dir_data)

    # THEN the expected start time is returned
    assert start_time == expected_time


@pytest.mark.parametrize(
    "run_dir_data, time_service, expected_time",
    [
        (
            "novaseq_x_flow_cell",
            "novaseq_x_sequencing_times_service",
            "novaseq_x_sequencing_end_time",
        ),
        (
            "novaseq_6000_pre_1_5_kits_flow_cell",
            "novaseq_6000_sequencing_times_service",
            "novaseq_6000_sequencing_end_time",
        ),
        (
            "hiseq_2500_dual_index_flow_cell",
            "hiseq_sequencing_times_service",
            "hiseq_sequencing_end_time",
        ),
    ],
)
def test_get_sequencing_end_time(run_dir_data, time_service, expected_time, request):
    # GIVEN run directory data and a time service
    run_dir_data = request.getfixturevalue(run_dir_data)
    time_service = request.getfixturevalue(time_service)
    expected_time = request.getfixturevalue(expected_time)

    # WHEN retrieving the start time
    start_time: datetime = time_service.get_end_time(run_dir_data)

    # THEN the expected start time is returned
    assert start_time == expected_time
