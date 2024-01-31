from typing import Callable

from cg.store.models import Case


class QualityController:
    @staticmethod
    def run_qc(case: Case, quality_checks: list[Callable]) -> bool:
        """
        Run the qc for the case.

        Returns:
            bool: True if the case passes the qc, False otherwise.

        """
        return all(quality_check(case) for quality_check in quality_checks)
