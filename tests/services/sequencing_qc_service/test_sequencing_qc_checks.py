from collections.abc import Callable
from unittest.mock import create_autospec

from cg.constants.constants import Workflow
from cg.services.sequencing_qc_service.quality_checks.checks import (
    SequencingQCCheck,
    get_sequencing_quality_check_for_case,
)
from cg.store.models import Case


def test_nallo_qc():
    # GIVEN a Nallo case
    case: Case = create_autospec(Case, data_analysis=Workflow.NALLO)

    # WHEN getting the sequencing qc check for the case
    qc_check: Callable = get_sequencing_quality_check_for_case(case)

    # THEN a yield based qc check was returned
    assert qc_check == SequencingQCCheck.CASE_PASSES_ON_YIELD
