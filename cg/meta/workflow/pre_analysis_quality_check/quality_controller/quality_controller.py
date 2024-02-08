from typing import Any, Callable

from cg.store.models import Case, Sample
from cg.store.store import Store


class QualityController:
    
    def __call__(self, store: Store) -> Any:
        store: Store = store
        
    @staticmethod
    def run_qc(obj: Case | Sample, quality_checks: list[Callable]) -> bool:
        """
        Run the qc for the case.

        Returns:
            bool: True if the case passes the qc, False otherwise.

        """
        return any(quality_check(obj) for quality_check in quality_checks)
