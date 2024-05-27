import logging
from typing import Callable

from cg.constants.constants import SequencingQCStatus
from cg.services.sequencing_qc_service.utils import qc_bool_to_status
from typing import Callable

from cg.store.models import Case, Sample
from cg.services.sequencing_qc_service.quality_checks.checks import (
    run_quality_checks,
    get_sequencing_quality_check_for_case,
    get_sample_sequencing_quality_check,
)
from cg.store.store import Store


class SequencingQCService:

    def __init__(self, store: Store):
        self.store = store

    def run_sequencing_qc(self) -> None:
        """Run sequencing QC for all pending or failed cases."""
        cases: list[Case] = self.store.get_cases_for_sequencing_qc()
        for case in cases:
            passes_qc: bool = self.case_pass_sequencing_qc(case)
            qc_status: SequencingQCStatus = qc_bool_to_status(passes_qc)
            self.store.update_sequencing_qc_status(case=case, status=qc_status)

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
