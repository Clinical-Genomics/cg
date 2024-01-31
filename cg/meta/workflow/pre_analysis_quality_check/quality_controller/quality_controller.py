from typing import Callable

from cg.store.models import Case, Sample


class CaseQualityController:
    
    @staticmethod
    def run_qc(case: Case, quality_checks: list[Callable]) -> bool:
        """
        Run the qc for the case.

        Returns:
            bool: True if the case passes the qc, False otherwise.

        """
        return all(quality_check(case) for quality_check in quality_checks)

class SampleQualityController:
    @staticmethod
    def run_qc(sample: Sample, quality_checks: list[Callable]) -> bool:
        """
        Run the qc for the sample.

        Returns:
            bool: True if the sample passes the qc, False otherwise.

        """
        return all(quality_check(sample) for quality_check in quality_checks)
