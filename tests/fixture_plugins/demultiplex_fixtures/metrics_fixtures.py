from datetime import datetime

import pytest

from cg.constants.devices import DeviceType
from cg.services.illumina_services.illumina_metrics_service.models import (
    IlluminaSampleSequencingMetricsDTO,
)


@pytest.fixture
def mapped_metric(timestamp_now: datetime):
    return IlluminaSampleSequencingMetricsDTO(
        sample_id="sample",
        type=DeviceType.ILLUMINA,
        flow_cell_lane=1,
        total_reads_in_lane=100,
        base_passing_q30_percent=0.9,
        base_mean_quality_score=30,
        yield_=100,
        yield_q30=0.9,
        created_at=timestamp_now,
    )


@pytest.fixture
def undetermined_metric(timestamp_now: datetime):
    return IlluminaSampleSequencingMetricsDTO(
        sample_id="sample",
        flow_cell_lane=1,
        type=DeviceType.ILLUMINA,
        total_reads_in_lane=100,
        base_passing_q30_percent=0.8,
        base_mean_quality_score=20,
        yield_=100,
        yield_q30=0.8,
        created_at=timestamp_now,
    )


@pytest.fixture
def combined_metric(timestamp_now: datetime):
    return IlluminaSampleSequencingMetricsDTO(
        sample_id="sample",
        flow_cell_lane=1,
        type=DeviceType.ILLUMINA,
        total_reads_in_lane=200,
        base_passing_q30_percent=0.85,
        base_mean_quality_score=25,
        yield_=200,
        yield_q30=0.85,
        created_at=timestamp_now,
    )
