from datetime import datetime
from unittest.mock import create_autospec

from cg.constants.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.store.models import Case, Sample


def test_unhandled_samples_response_from_samples():
    case = create_autospec(Case)
    # GIVEN a list of database samples
    sample1 = create_autospec(
        Sample,
        internal_id="sample_1",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        original_workflow=Workflow.RAREDISEASE,
        ticket_from_original_order=589365,
    )
    sample2 = create_autospec(
        Sample,
        internal_id="sample_2",
        last_sequenced_at=datetime.now(),
        lims_status=LimsStatus.TOP_UP,
        original_workflow=Workflow.RAREDISEASE,
        ticket_from_original_order=589365,
    )
    # WHEN creating an UnhandledSampleResponse from samples
    # THEN the response is as expected
