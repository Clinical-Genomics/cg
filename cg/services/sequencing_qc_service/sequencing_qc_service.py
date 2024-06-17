from typing import Callable

from cg.store.models import Case, Sample
from cg.services.sequencing_qc_service.quality_checks.checks import (
    run_quality_checks,
    get_sequencing_quality_check_for_case,
    get_sample_sequencing_quality_check,
)


class SequencingQCService:

    @staticmethod
    def case_pass_sequencing_qc(case: Case) -> bool:
        """
        Run the QC for the case or sample.
        """
        sequencing_quality_check: Callable = get_sequencing_quality_check_for_case(case)
        return run_quality_checks(quality_checks=[sequencing_quality_check], case=case)

    @staticmethod
    def sample_pass_sequencing_qc(sample: Sample) -> bool:
        """
        Run the sequencing QC for a sample.
        """
        sample_sequencing_quality_check: Callable = get_sample_sequencing_quality_check()
        return run_quality_checks(quality_checks=[sample_sequencing_quality_check], sample=sample)
