from typing import Callable

from cg.store.models import Case, Sample
from cg.services.quality_controller.quality_checks.checks import (
    run_quality_checks,
    get_sequencing_quality_checks_for_case,
    get_sample_sequencing_quality_checks,
)


class QualityController:
    """Quality controller class. This class is used to run the quality checks for the samples and cases."""

    @staticmethod
    def case_pass_sequencing_qc(case: Case) -> bool:
        """
        Run the qc for the case or sample.
        """
        sequencing_quality_checks: list[Callable] = get_sequencing_quality_checks_for_case(case)

        return run_quality_checks(quality_checks=sequencing_quality_checks, case=case)

    @staticmethod
    def sample_pass_sequencing_qc(sample: Sample) -> bool:
        """
        Run the sequencing QC for a sample.
        """
        sample_sequencing_quality_checks: Callable = get_sample_sequencing_quality_checks()

        return run_quality_checks(quality_checks=sample_sequencing_quality_checks, sample=sample)
