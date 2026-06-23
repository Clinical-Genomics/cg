from datetime import datetime
from unittest.mock import create_autospec

import pytest

from cg.constants.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.constants.priority import PriorityTerms
from cg.server.dto.samples.samples_response import UnhandledSample, UnhandledSamplesResponse
from cg.store.models import Sample


@pytest.mark.freeze_time
def test_unhandled_samples_response_from_samples():
    # GIVEN a list of database samples
    sample_1 = create_autospec(
        Sample,
        delivering_case_internal_id="case_1",
        internal_id="sample_1",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        priority_of_case_that_delivers=PriorityTerms.RESEARCH,
        ticket_id_from_original_order=123456,
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
    )
    sample_2 = create_autospec(
        Sample,
        delivering_case_internal_id="case_2",
        internal_id="sample_2",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        priority_of_case_that_delivers=PriorityTerms.EXPRESS,
        ticket_id_from_original_order=123456,
        workflow_of_case_that_delivers=Workflow.RAREDISEASE,
    )
    # WHEN creating an UnhandledSampleResponse from samples
    response = UnhandledSamplesResponse.from_samples(samples=[sample_1, sample_2], total=15)

    # THEN the response is as expected
    assert response == UnhandledSamplesResponse(
        samples=[
            UnhandledSample(
                case_id="case_1",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                sample_id="sample_1",
                case_priority=PriorityTerms.RESEARCH,
                ticket=123456,
                workflow=Workflow.RAREDISEASE,
            ),
            UnhandledSample(
                case_id="case_2",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                sample_id="sample_2",
                case_priority=PriorityTerms.EXPRESS,
                ticket=123456,
                workflow=Workflow.RAREDISEASE,
            ),
        ],
        total=15,
    )


@pytest.mark.freeze_time
def test_unhandled_samples_response_from_samples_without_ticket_id_and_workflow():
    # GIVEN a sample with no original workflow nor ticket id
    sample_1 = create_autospec(
        Sample,
        delivering_case_internal_id="case_1",
        internal_id="sample_1",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        priority_of_case_that_delivers=PriorityTerms.STANDARD,
        ticket_id_from_original_order=None,
        workflow_of_case_that_delivers=None,
    )

    # WHEN getting the unhandled samples response
    unhandled_samples_response = UnhandledSamplesResponse.from_samples(samples=[sample_1], total=10)

    # THEN the workflow and ticket should be "unknown"
    assert unhandled_samples_response == UnhandledSamplesResponse(
        samples=[
            UnhandledSample(
                case_id="case_1",
                last_sequenced_at=datetime.now(),
                lims_status=LimsStatus.TOP_UP,
                sample_id="sample_1",
                case_priority=PriorityTerms.STANDARD,
                ticket="unknown",
                workflow="unknown",
            ),
        ],
        total=10,
    )
