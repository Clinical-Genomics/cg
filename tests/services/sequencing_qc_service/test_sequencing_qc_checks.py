from collections.abc import Callable
from unittest.mock import create_autospec

from cg.constants.constants import Workflow
from cg.constants.devices import DeviceType
from cg.services.sequencing_qc_service.quality_checks.checks import (
    SequencingQCCheck,
    get_sequencing_quality_check_for_case,
)
from cg.store.models import Case, Sample, SampleRunMetrics


def test_nallo_qc():
    # GIVEN a Nallo case
    case: Case = create_autospec(Case, data_analysis=Workflow.NALLO)

    # WHEN getting the sequencing qc check for the case
    qc_check: Callable = get_sequencing_quality_check_for_case(case)

    # THEN a yield based qc check was returned
    assert qc_check == SequencingQCCheck.CASE_PASSES_ON_YIELD


def test_raw_data_read_based_qc_case():
    # GIVEN a Raw Data case with Illumina sample sequencing metrics
    sample: Sample = create_autospec(
        Sample,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )
    case: Case = create_autospec(Case, data_analysis=Workflow.RAW_DATA, samples=[sample])

    # WHEN getting the sequencing qc check for the case
    qc_check: Callable = get_sequencing_quality_check_for_case(case)

    # THEN a read based qc check was returned
    # TODO: Double check the RML case
    assert qc_check == SequencingQCCheck.CASE_PASSES_ON_READS
