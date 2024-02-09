from typing import Callable

from cg.store.models import Case, Sample


class QualityController:
    @staticmethod
    def run_qc(obj: Case | Sample, quality_checks: list[Callable]) -> bool:
        """
        Run the qc for the case.

        Returns:
            bool: True if the case passes the qc, False otherwise.

        """
        return any(quality_check(obj) for quality_check in quality_checks)
