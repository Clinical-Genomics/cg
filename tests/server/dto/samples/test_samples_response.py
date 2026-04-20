from datetime import datetime
from unittest.mock import create_autospec

import pytest

from cg.constants.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.server.dto.samples.samples_response import UnhandledSample, UnhandledSamplesResponse
from cg.store.models import Sample


@pytest.mark.freeze_time
def test_unhandled_samples_response_from_samples():
    # GIVEN a list of database samples
    sample_1 = create_autospec(
        Sample,
        internal_id="sample_1",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        original_workflow=Workflow.RAREDISEASE,
        ticket_id_from_original_order=123456,
    )
    sample_2 = create_autospec(
        Sample,
        internal_id="sample_2",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        original_workflow=Workflow.RAREDISEASE,
        ticket_id_from_original_order=123456,
    )
    # WHEN creating an UnhandledSampleResponse from samples
    response = UnhandledSamplesResponse.from_samples(samples=[sample_1, sample_2], total=15)

    # THEN the response is as expected
    assert response == UnhandledSamplesResponse(
        samples=[
            UnhandledSample(
                internal_id="sample_1",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                workflow=Workflow.RAREDISEASE,
                ticket=123456,
            ),
            UnhandledSample(
                internal_id="sample_2",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                workflow=Workflow.RAREDISEASE,
                ticket=123456,
            ),
        ],
        total=15,
    )


@pytest.mark.freeze_time
def test_unhandled_samples_response_from_samples_without_ticket_id_and_workflow():
    # GIVEN a sample with no original workflow nor ticket id
    sample_1 = create_autospec(
        Sample,
        internal_id="sample_1",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        original_workflow=None,
        ticket_id_from_original_order=None,
    )

    # WHEN getting the unhandled samples response
    unhandled_samples_response = UnhandledSamplesResponse.from_samples(samples=[sample_1], total=10)

    # THEN the workflow and ticket should be "unknown"
    assert unhandled_samples_response == UnhandledSamplesResponse(
        samples=[
            UnhandledSample(
                internal_id="sample_1",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                workflow="unknown",
                ticket="unknown",
            ),
        ],
        total=10,
    )
